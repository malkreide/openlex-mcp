"""
HTTP-Client für ZH-Lex Metadaten
==================================
Ruft aktuelle Metadaten und PDF-Links von der offiziellen
ZH-Lex-Website (zh.ch) ab.

Endpunkte:
  - zh.ch Gesetzessammlung HTML-Seiten → Metadaten-Extraktion
  - LexFind.ch → PDF-Downloads und Versionen

Hinweis: ZH-Lex hat keine offizielle API. Die Metadaten werden
aus den HTML-Seiten extrahiert (Web Scraping light).
"""

from __future__ import annotations

import asyncio
import random
import re
import time
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import httpx

from openlex_mcp import net

from . import __version__

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

ZHLEX_BASE = "https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung"
# Permalink-Dienst: stabile URL pro Ordnungsnummer. 'lawcollection-directlink'
# leitet (302) auf die aktuelle datierte Fassung unter www.zh.ch weiter — nötig,
# weil www.zh.ch keine undatierte Erlass-URL bereitstellt. Löst den früheren
# Permalink http://www.zhlex.zh.ch/Erlass.html ab, der von zh.ch umgestellt
# wurde und nun 404 liefert.
ZHLEX_PERMALINK_BASE = "https://www.zhlex.zh.ch/bin/zhweb/publish/lawcollection-directlink"
LEXFIND_BASE = "https://www.lexfind.ch"

REQUEST_TIMEOUT = 30.0
# HTTP-Header müssen ASCII sein (httpx lehnt Umlaute ab) — daher "Zuerich".
USER_AGENT = f"openlex-mcp/{__version__} (Kanton Zuerich Rechtssammlung MCP Server)"

# Transiente Netzfehler (Timeout/Verbindung) gegen zh.ch werden mit
# exponentiellem Backoff erneut versucht — der Dienst ist zeitweise langsam
# oder kurz nicht erreichbar. Deterministische Fehler (404, HTTP-Status,
# Egress-Block) werden NICHT wiederholt.
# --- Retry-Politik gegenüber der Quelle (ARCH-014) ---------------------------
# Drei Fragen: *was* wiederholt wird, *wie schnell* und *wie lange*. Die erste
# beantwortet die Schleife in `fetch_law_metadata` (5xx, 429 und Netzfehler ja;
# jedes andere 4xx nein), die beiden anderen diese Konstanten.

METADATA_MAX_ATTEMPTS = 3
METADATA_BACKOFF_BASE = 1.0  # Leiter vor dem Jitter: 1 s, 2 s

# Deckel auf den GESAMTEN Aufruf — alle Versuche und alle Wartezeiten zusammen.
# Eine Versuchszahl ist keine Grenze: Drei Versuche gegen einen Upstream, der
# die vollen REQUEST_TIMEOUT (30 s) braucht, sind anderthalb Minuten in einem
# Tool-Aufruf, und METADATA_MAX_ATTEMPTS sagt das nirgends. Der Anker ist
# gemessen, nicht geraten: Das Python-MCP-SDK liefert MCP_DEFAULT_TIMEOUT =
# 30.0 aus, also lassen 25 s Luft für Framing und Parsing. Jenseits des
# Client-Timeouts hört niemand mehr zu — die Arbeit läuft weiter, die Last
# landet bei der Quelle, und das Ergebnis geht ins Leere.
METADATA_TOTAL_BUDGET = 25.0

# Deckel auf eine einzelne Wartezeit. Begrenzt die exponentielle Leiter und
# einen `Retry-After`, den die Quelle senden darf und den wir nicht absitzen
# müssen.
METADATA_MAX_DELAY = 20.0

# Streuung. Ohne sie wiederholen alle Clients, die denselben Ausfall getroffen
# haben, im Gleichtakt — die Last kommt als Welle zurück, genau wenn sich die
# Quelle erholt, und der Retry-Sturm verlängert den Ausfall, den er überbrücken
# sollte.
METADATA_JITTER_SPREAD = 0.5  # exponentielle Wartezeiten landen in [0.5x, 1.5x]

# Auf einen `Retry-After` angewandt, und bewusst einseitig: Die Quelle hat
# gesagt, wann sie wieder mag — später ist höflich, früher ignoriert genau den
# Wert, den man gerade liest.
METADATA_RETRY_AFTER_JITTER = 0.25  # landet in [1.0x, 1.25x]

# Status-Codes, die einen sinnvollen `Retry-After` tragen (RFC 9110 §10.2.3).
RETRY_AFTER_STATUSES = frozenset({429, 503})

# Indirektion, damit Tests die Wartezeit nullen können, ohne `asyncio.sleep`
# selbst zu patchen. Ein `monkeypatch.setattr(api_client.asyncio, "sleep", ...)`
# sähe lokal aus und ist es nicht: `api_client.asyncio` *ist* das
# stdlib-Modul, der Patch legt das Schlafen prozessweit still — samt fremder
# Tests, die damit dem Event-Loop das Wort geben und danach nichts mehr messen.
_sleep = asyncio.sleep


def _parse_retry_after(resp: httpx.Response | None) -> float | None:
    """Sekunden laut ``Retry-After`` der Antwort, oder ``None``.

    RFC 9110 §10.2.3 erlaubt zwei Formen — Sekundenzahl (``120``) und
    HTTP-Datum. Beide kommen vor, also werden beide gelesen. Alles
    Unlesbare ergibt ``None``, und der Aufrufer fällt auf die eigene Kurve
    zurück: Ein kaputter Header darf auf dem Fehlerpfad — dem einen Pfad, der
    ohnehin schon schlecht läuft — kein zweiter Fehler werden.
    """
    if resp is None or resp.status_code not in RETRY_AFTER_STATUSES:
        return None
    raw = (resp.headers.get("retry-after") or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        return float(raw)
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:  # RFC-9110-Daten sind GMT; ein naives meint UTC
        when = when.replace(tzinfo=UTC)
    return max(
        0.0, (when - datetime.now(UTC)).total_seconds()
    )  # Datum in der Vergangenheit -> jetzt


def _retry_delay(attempt: int, resp: httpx.Response | None) -> float:
    """Sekunden vor ``attempt`` (1-basiert für die erste Wiederholung).

    Der Deckel umschliesst den Jitter und nicht umgekehrt. ``min(deckel, base)
    * jitter`` und ``min(deckel, base * jitter)`` enthalten beide einen Deckel
    und einen Jitter; nur das zweite ist begrenzt — ein auf 20 s gedeckelter
    Wert, anschliessend mit bis zu 1.5 multipliziert, landet bei 30 s, und die
    Konstante behauptete eine Schranke, die sie nicht einhält. Diese
    Reihenfolge steckte in sechs Portfolio-Servern.
    """
    hinted = _parse_retry_after(resp)
    if hinted is not None:
        return min(
            hinted * (1.0 + random.random() * METADATA_RETRY_AFTER_JITTER),
            METADATA_MAX_DELAY,
        )
    return min(
        METADATA_BACKOFF_BASE
        * 2 ** (attempt - 1)
        * (1.0 - METADATA_JITTER_SPREAD + random.random() * 2 * METADATA_JITTER_SPREAD),
        METADATA_MAX_DELAY,
    )


# ZH-Lex URL-Muster für Ordnungsnummern
# Konvertierung: 412.100 → 412_100
_SR_TO_URL_PATTERN = re.compile(r"\.")


# ---------------------------------------------------------------------------
# URL-Builder
# ---------------------------------------------------------------------------


def build_zhlex_search_url(sr_number: str) -> str:
    """Baut die ZH-Lex URL für eine Ordnungsnummer.

    Args:
        sr_number: z.B. '412.100'

    Returns:
        URL zur ZH-Lex Übersichtsseite für dieses Gesetz.
    """
    # Ordnungsnummer für URL konvertieren: 412.100 → 412_100
    sr_url = _SR_TO_URL_PATTERN.sub("_", sr_number)
    return f"{ZHLEX_BASE}/zhlex-ls/erlass-{sr_url}.html"


def build_zhlex_permalink_url(sr_number: str) -> str:
    """Baut den stabilen Ordnungsnummer-Permalink auf www.zhlex.zh.ch.

    Args:
        sr_number: z.B. '412.100'

    Returns:
        URL zur aktuellen Fassung des Erlasses (leitet auf www.zh.ch weiter).
        Im Gegensatz zur datierten www.zh.ch-URL ist dieser Link allein aus der
        Ordnungsnummer ableitbar und stabil.
    """
    return f"{ZHLEX_PERMALINK_BASE}?Open&Ordnr={sr_number}"


def build_lexfind_url(sr_number: str) -> str:
    """Baut die LexFind-URL für ein ZH-Gesetz.

    Args:
        sr_number: z.B. '412.100'

    Returns:
        URL zur LexFind-Seite (approximativ).
    """
    return f"{LEXFIND_BASE}/fe/de/tol/search?query={sr_number}&canton=26"


# ---------------------------------------------------------------------------
# HTTP-Client
# ---------------------------------------------------------------------------


async def _get_client() -> httpx.AsyncClient:
    """Deprecated-Alias: gibt den geteilten Client zurück (siehe get_client)."""
    return get_client()


# Prozessweiter, geteilter HTTP-Client — SDK-001: kein neuer Client pro
# Tool-Call. Erstellt beim ersten Gebrauch, geschlossen im Lifespan-Shutdown.
_client: httpx.AsyncClient | None = None


def _build_client() -> httpx.AsyncClient:
    # follow_redirects=False: Redirects werden von net.safe_get manuell
    # verfolgt, damit jedes Ziel die SSRF-/Egress-Prüfkette durchläuft.
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=False,
    )


def get_client() -> httpx.AsyncClient:
    """Gibt den geteilten httpx-Client zurück (lazy erstellt / wiederverwendet)."""
    global _client
    if _client is None or _client.is_closed:
        _client = _build_client()
    return _client


async def aclose_client() -> None:
    """Schliesst den geteilten Client (aufgerufen im Lifespan-Shutdown)."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


async def fetch_zhlex_metadata(sr_number: str) -> dict:
    """Ruft Metadaten von zh.ch für ein bestimmtes Gesetz ab.

    Extrahiert aus der HTML-Seite:
    - Seitentitel
    - Verfügbare PDF-Links
    - Änderungsdaten
    - Geltungsstatus

    Args:
        sr_number: Ordnungsnummer, z.B. '412.100'

    Returns:
        Dict mit Metadaten oder Fehlermeldung.
    """
    # Stabiler Ordnungsnummer-Permalink (www.zhlex.zh.ch) statt der datierten
    # www.zh.ch-URL — letztere ist allein aus der Ordnungsnummer nicht ableitbar.
    # Der Permalink leitet via Redirect auf die aktuelle Fassung weiter; jeder
    # Redirect-Hop durchläuft die volle net.safe_get-Prüfkette erneut.
    url = build_zhlex_permalink_url(sr_number)

    # Geteilten Client wiederverwenden (nicht schliessen — Lifespan-scoped).
    # net.safe_get erzwingt HTTPS (HTTP nur für gelistete Hosts) + Egress-Allow-
    # List + SSRF-IP-Block + DNS-Pinning.
    client = get_client()

    # Transiente Fehler lösen einen erneuten Versuch aus; der zuletzt gesehene
    # bestimmt die Fehlermeldung, falls alle Versuche scheitern.
    last_transient: httpx.HTTPError | None = None
    last_response: httpx.Response | None = None
    deadline = time.monotonic() + METADATA_TOTAL_BUDGET
    for attempt in range(METADATA_MAX_ATTEMPTS):
        if attempt > 0:
            delay = _retry_delay(attempt, last_response)
            # Eine Wartezeit, die das Budget überdauert, ist eine Wartezeit für
            # niemanden: Der Aufrufer hat aufgegeben, bevor sie endet.
            if delay >= deadline - time.monotonic():
                break
            await _sleep(delay)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        try:
            # `asyncio.timeout` ist die Wanduhr-Deadline, die das Budget
            # zusagt. Das httpx-Timeout greift pro Operation und beginnt mit
            # jedem Chunk von vorn — es begrenzt den Schritt, nicht den Aufruf.
            async with asyncio.timeout(remaining):
                response, final_url = await net.safe_get(client, url)

                if response.status_code == 404:
                    return {
                        "found": False,
                        "sr_number": sr_number,
                        "url": final_url,
                        "message": f"Gesetz {sr_number} nicht auf zh.ch gefunden.",
                    }

                response.raise_for_status()
                html = response.text

                # Basis-Metadaten aus HTML extrahieren
                metadata = _extract_metadata_from_html(html, sr_number)
                metadata["url"] = final_url
                metadata["found"] = True
                return metadata

        except TimeoutError as e:  # Budget weg, nicht bloss dieser Versuch
            last_transient = httpx.TimeoutException(str(e))
            break
        except (httpx.TimeoutException, httpx.ConnectError, httpx.RequestError) as e:
            # Transient: erneut versuchen (die Wartezeit steht oben in der
            # Schleife). `RequestError` ist die Oberklasse — ein
            # Verbindungsabbruch, der weder Timeout noch ConnectError heisst,
            # ist derselbe Fall und blieb bisher ungedeckt.
            last_transient = e
            last_response = None
            continue
        except net.EgressError as e:
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": f"Egress blockiert: {e}",
            }
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            # 5xx und 429 sind eine Aussage über den Moment, nicht über die
            # Anfrage — bisher endeten sie hier sofort, ohne einen zweiten
            # Versuch. Alles andere im 4xx-Bereich wird auch beim dritten Mal
            # kein 200.
            if status >= 500 or status == 429:
                last_transient = e
                last_response = e.response
                continue
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": f"HTTP {status}",
            }
        except Exception as e:
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": str(e),
            }

    # Alle Versuche an transienten Netzfehlern gescheitert.
    if isinstance(last_transient, httpx.HTTPStatusError):
        error = f"zh.ch antwortet mit HTTP {last_transient.response.status_code}"
    elif isinstance(last_transient, httpx.TimeoutException):
        error = "Timeout bei zh.ch"
    else:
        error = "Verbindung zu zh.ch fehlgeschlagen"
    return {
        "found": False,
        "sr_number": sr_number,
        "url": url,
        "error": error,
    }


def _extract_metadata_from_html(html: str, sr_number: str) -> dict:
    """Extrahiert Metadaten aus einer ZH-Lex HTML-Seite.

    Einfache Regex-basierte Extraktion (kein BeautifulSoup nötig).
    """
    metadata: dict = {"sr_number": sr_number}

    # Seitentitel
    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        title = title_match.group(1).strip()
        # "Kanton Zürich - " Prefix entfernen
        title = re.sub(r"^Kanton Zürich\s*[-–]\s*", "", title)
        metadata["page_title"] = title

    # PDF-Links finden
    pdf_links = re.findall(
        r'href="([^"]*\.pdf[^"]*)"',
        html,
        re.IGNORECASE,
    )
    if pdf_links:
        # Relative URLs zu absoluten machen
        full_links = []
        for link in pdf_links:
            if link.startswith("http"):
                full_links.append(link)
            elif link.startswith("/"):
                full_links.append(f"https://www.zh.ch{link}")
        metadata["pdf_links"] = list(set(full_links))[:5]  # Max 5

    # Datum der letzten Änderung (typisches Muster auf zh.ch)
    date_match = re.search(
        r"(?:Inkrafttreten|In Kraft seit|Änderung vom)\s*(\d{1,2}\.\s*\w+\s*\d{4})",
        html,
    )
    if date_match:
        metadata["last_change"] = date_match.group(1).strip()

    # Erlassdatum
    enactment_match = re.search(
        r"(?:Erlass vom|Beschluss vom|vom)\s*(\d{1,2}\.\s*\w+\s*\d{4})",
        html,
    )
    if enactment_match:
        metadata["enactment_date"] = enactment_match.group(1).strip()

    return metadata


# ---------------------------------------------------------------------------
# Fehlerbehandlung
# ---------------------------------------------------------------------------


def handle_error(e: Exception, context: str = "") -> str:
    """Einheitliche, handlungsweisende Fehlermeldungen."""
    prefix = f"Fehler bei {context}: " if context else "Fehler: "

    if isinstance(e, httpx.HTTPStatusError):
        code = e.response.status_code
        if code == 404:
            return f"{prefix}Ressource nicht gefunden (HTTP 404)."
        if code == 403:
            return f"{prefix}Zugriff verweigert (HTTP 403)."
        if code == 429:
            return f"{prefix}Zu viele Anfragen. Bitte kurz warten."
        if code == 503:
            return f"{prefix}zh.ch vorübergehend nicht verfügbar."
        return f"{prefix}HTTP-Fehler {code}."

    if isinstance(e, (httpx.TimeoutException, httpx.ReadTimeout)):
        return f"{prefix}Zeitüberschreitung. Bitte erneut versuchen."

    if isinstance(e, httpx.ConnectError):
        return f"{prefix}Verbindung fehlgeschlagen. Internetverbindung prüfen."

    # OBS-002: keine Internals (Exception-Typ/Message, Stacktraces, SQL) ans
    # LLM. Der Originalfehler wird vom Aufrufer nach stderr geloggt.
    return f"{prefix}Ein unerwarteter interner Fehler ist aufgetreten."
