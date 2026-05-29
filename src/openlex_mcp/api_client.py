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

import re

import httpx

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

ZHLEX_BASE = "https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung"
LEXFIND_BASE = "https://www.lexfind.ch"

REQUEST_TIMEOUT = 30.0
# HTTP-Header müssen ASCII sein (httpx lehnt Umlaute ab) — daher "Zuerich".
USER_AGENT = "openlex-mcp/0.1.0 (Kanton Zuerich Rechtssammlung MCP Server)"

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
    """Erstellt einen konfigurierten httpx-Client."""
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


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
    url = build_zhlex_search_url(sr_number)

    async with await _get_client() as client:
        try:
            response = await client.get(url)

            if response.status_code == 404:
                return {
                    "found": False,
                    "sr_number": sr_number,
                    "url": url,
                    "message": f"Gesetz {sr_number} nicht auf zh.ch gefunden.",
                }

            response.raise_for_status()
            html = response.text

            # Basis-Metadaten aus HTML extrahieren
            metadata = _extract_metadata_from_html(html, sr_number)
            metadata["url"] = str(response.url)
            metadata["found"] = True
            return metadata

        except httpx.HTTPStatusError as e:
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": f"HTTP {e.response.status_code}",
            }
        except httpx.TimeoutException:
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": "Timeout bei zh.ch",
            }
        except Exception as e:
            return {
                "found": False,
                "sr_number": sr_number,
                "url": url,
                "error": str(e),
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

    return f"{prefix}{type(e).__name__}: {e}"
