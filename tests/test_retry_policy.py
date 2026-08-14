"""Tests für die Retry-Politik gegenüber zh.ch (ARCH-014).

Ein Portfolio-Durchlauf des Audit-Katalogs am 2026-08-07 las die Schleife in
``fetch_law_metadata`` von Hand. Vier Eigenschaften fehlten: 5xx wurde gar nicht
wiederholt, der Backoff war deterministisch, ``Retry-After`` wurde nicht
gelesen, und es gab keine Zeitgrenze.

Jede Eigenschaft hat hier eine Gegenprobe — die vorherige Fassung ist der
ehrliche Massstab, weil sie bis zu diesem Branch in Produktion war.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from email.utils import format_datetime

import httpx
import pytest

from openlex_mcp import api_client

SR = "412.100"


def _resp(status: int, retry_after: str | None = None) -> httpx.Response:
    headers = {"Retry-After": retry_after} if retry_after is not None else {}
    # Die Request-Instanz gehört dran: ohne sie wirft `raise_for_status()`
    # einen RuntimeError statt des HTTPStatusError, den der Code erwartet —
    # der Test würde dann den falschen Zweig messen.
    return httpx.Response(
        status,
        headers=headers,
        text="<html></html>",
        request=httpx.Request("GET", "https://www.zhlex.zh.ch/x"),
    )


def _stub_safe_get(monkeypatch, responses: list):
    """Ersetzt ``net.safe_get`` durch eine Folge von Antworten oder Fehlern."""
    calls: list[int] = []

    async def _fake(client, url):
        item = responses[min(len(calls), len(responses) - 1)]
        calls.append(1)
        if isinstance(item, BaseException):
            raise item
        return item, url

    monkeypatch.setattr(api_client.net, "safe_get", _fake)
    monkeypatch.setattr(api_client, "get_client", lambda: None)
    return calls


# --- Retry-After: überhaupt gelesen, und beide RFC-9110-Formen ---------------


def test_retry_after_liest_sekundenzahl():
    assert api_client._parse_retry_after(_resp(429, "120")) == 120.0


def test_retry_after_liest_ein_http_datum():
    when = datetime.now(UTC) + timedelta(seconds=60)
    got = api_client._parse_retry_after(_resp(503, format_datetime(when, usegmt=True)))
    assert got is not None
    assert 55 <= got <= 61


def test_retry_after_behandelt_vergangenes_datum_als_jetzt():
    when = datetime.now(UTC) - timedelta(hours=1)
    got = api_client._parse_retry_after(_resp(503, format_datetime(when, usegmt=True)))
    assert got == 0.0


def test_retry_after_liest_naives_datum_als_gmt_nicht_lokal():
    when = datetime.now(UTC) + timedelta(seconds=30)
    got = api_client._parse_retry_after(_resp(503, when.strftime("%a, %d %b %Y %H:%M:%S")))
    assert got is not None
    assert 25 <= got <= 31


@pytest.mark.parametrize("raw", ["", "   ", "bald", "kein-datum"])
def test_unlesbarer_retry_after_faellt_zurueck_statt_zu_werfen(raw):
    # Der Fehlerpfad läuft ohnehin schon schlecht; ein kaputter Header darf
    # dort kein zweiter Fehler werden.
    assert api_client._parse_retry_after(_resp(429, raw)) is None


def test_retry_after_wird_ignoriert_wo_er_nichts_bedeutet():
    assert api_client._parse_retry_after(_resp(500, "120")) is None
    assert api_client._parse_retry_after(None) is None


# --- Jitter und der Deckel, der danach greifen muss --------------------------


def test_die_exponentielle_wartezeit_ist_gestreut():
    draws = {api_client._retry_delay(1, None) for _ in range(50)}
    assert len(draws) > 1, "ein Gleichtakt-Backoff kommt als Welle zurück"


def test_ein_retry_after_wird_einseitig_gestreut():
    draws = [api_client._retry_delay(1, _resp(429, "10")) for _ in range(50)]
    assert len(set(draws)) > 1
    assert all(10.0 <= d <= 12.5 for d in draws), sorted(draws)[:3]


def test_der_deckel_ist_eine_echte_schranke_kein_mittelwert():
    # Jitter ist zufällig — eine Ziehung beweist nichts.
    for attempt in range(1, 9):
        for _ in range(25):
            assert api_client._retry_delay(attempt, None) <= api_client.METADATA_MAX_DELAY
            assert (
                api_client._retry_delay(attempt, _resp(429, "86400"))
                <= api_client.METADATA_MAX_DELAY
            )


def test_deckel_vor_dem_jitter_waere_keine_schranke():
    """Gegenprobe zur Reihenfolge, damit der Test darüber fallen kann."""
    broken = min(api_client.METADATA_BACKOFF_BASE * 2**7, api_client.METADATA_MAX_DELAY) * 1.5
    assert broken > api_client.METADATA_MAX_DELAY


# --- Was wiederholt wird -----------------------------------------------------


async def test_ein_503_wird_wiederholt(monkeypatch):
    """Der Kernbefund: vorher endete ein 5xx sofort als Fehler-Dict."""
    calls = _stub_safe_get(monkeypatch, [_resp(503), _resp(200)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is True
    assert len(calls) == 2


async def test_ein_429_wird_wiederholt(monkeypatch):
    calls = _stub_safe_get(monkeypatch, [_resp(429), _resp(200)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is True
    assert len(calls) == 2


async def test_ein_403_wird_nicht_wiederholt(monkeypatch):
    calls = _stub_safe_get(monkeypatch, [_resp(403)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is False
    assert result["error"] == "HTTP 403"
    assert len(calls) == 1, "auch der dritte Versuch macht aus einem 403 kein 200"


async def test_ein_404_ist_eine_antwort_kein_fehler(monkeypatch):
    calls = _stub_safe_get(monkeypatch, [_resp(404)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is False
    assert "nicht auf zh.ch gefunden" in result["message"]
    assert len(calls) == 1


async def test_ein_verbindungsfehler_wird_wiederholt(monkeypatch):
    calls = _stub_safe_get(monkeypatch, [httpx.ConnectError("refused"), _resp(200)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is True
    assert len(calls) == 2


async def test_ein_allgemeiner_requesterror_wird_wiederholt(monkeypatch):
    """Die Oberklasse war ungedeckt: nur TimeoutException und ConnectError.

    Ein Verbindungsabbruch, der weder so noch so heisst — etwa
    ``httpx.ReadError`` — endete vorher im ``except Exception``-Zweig als
    Fehler-Dict, ohne einen zweiten Versuch.
    """
    calls = _stub_safe_get(monkeypatch, [httpx.ReadError("abgerissen"), _resp(200)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is True
    assert len(calls) == 2


async def test_die_versuche_sind_begrenzt(monkeypatch):
    calls = _stub_safe_get(monkeypatch, [_resp(503)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is False
    assert "HTTP 503" in result["error"]
    assert len(calls) == api_client.METADATA_MAX_ATTEMPTS


# --- Das Budget, an der Wanduhr gemessen -------------------------------------


async def test_eine_langsame_antwort_wird_von_der_wanduhr_geschnitten(monkeypatch):
    """Die Zusicherung, die eine Fake-Uhr nicht widerlegen kann.

    Eine Uhr, die nur beim Schlafen vorrückt, kann eine Aussage über *echte*
    Zeit nicht widerlegen: Der Code, der die Wanduhr ignoriert, schläft nicht,
    also vergeht keine Zeit, also bleibt die kaputte Fassung grün. Dieser Test
    schläft deshalb echt — bewusst, und als einziger hier.
    """
    monkeypatch.setattr(api_client, "METADATA_TOTAL_BUDGET", 0.05)

    async def _slow(client, url):
        await asyncio.sleep(0.30)
        return _resp(200), url

    monkeypatch.setattr(api_client.net, "safe_get", _slow)
    monkeypatch.setattr(api_client, "get_client", lambda: None)

    started = time.monotonic()
    result = await api_client.fetch_zhlex_metadata(SR)
    assert time.monotonic() - started < 0.25, "REQUEST_TIMEOUT ist kein Budget"
    assert result["found"] is False


async def test_eine_wartezeit_ueber_dem_budget_wird_nicht_genommen(monkeypatch):
    monkeypatch.setattr(api_client, "METADATA_TOTAL_BUDGET", 1.0)
    monkeypatch.setattr(api_client, "_retry_delay", lambda *_a, **_k: 999.0)
    calls = _stub_safe_get(monkeypatch, [_resp(503)])
    result = await api_client.fetch_zhlex_metadata(SR)
    assert result["found"] is False
    assert len(calls) == 1


# --- Die Naht, und warum sie nicht `asyncio.sleep` ist -----------------------


async def test_die_fixture_laesst_das_echte_asyncio_sleep_in_ruhe():
    """Bewacht die Naht, die die autouse-Fixture patcht.

    ``monkeypatch.setattr(api_client.asyncio, "sleep", ...)`` sähe lokal aus
    und legt das Schlafen prozessweit still — samt fremder Tests, die damit dem
    Event-Loop das Wort geben und danach nichts mehr messen. Genau so ist in
    ``srgssr-mcp`` eine Parallelitäts-Prüfung eingebrochen, ohne rot zu werden.
    """
    started = time.monotonic()
    await asyncio.sleep(0.05)
    assert time.monotonic() - started >= 0.04, "asyncio.sleep ist prozessweit ausser Kraft"


# --- Und die andere Haelfte: dass die Fixture die Wartezeit wirklich nullt ---
#
# Der Test oben bewacht, was die Fixture *nicht* treffen darf. Er sagt nichts
# darueber, ob sie ueberhaupt etwas bewirkt: Nimmt man sie heraus, bleiben alle
# Tests gruen, nur langsamer (4.97 s statt 0.60 s in `test_api_client.py`).
# Genau das ist die Lage, vor der CLAUDE.md warnt — eine Mechanik ohne
# Zusicherung. Die beiden Tests hier stellen sie her.
#
# Gemessen wird an der Wanduhr, denn nur sie kann die Aussage widerlegen. Eine
# Fake-Uhr, die beim Schlafen vorrueckt, wuerde auch die kaputte Fassung gruen
# lassen. Der Jitter wird bewusst NICHT festgenagelt: `api_client.random` *ist*
# das stdlib-Modul, ein Patch darauf haette denselben prozessweiten Effekt wie
# der auf `asyncio.sleep`. Stattdessen haengen die Schranken an der garantierten
# Untergrenze der Leiter, die unabhaengig vom Zufall gilt.

# Lang genug, dass eine echte Wartezeit unuebersehbar ist, und kurz genug, dass
# ein Fehlschlag die Suite nicht aufhaelt.
_SPUERBAR = 1.0


def _echte_wartezeit_untergrenze() -> float:
    """Was ein erschoepfter Retry-Pfad mindestens real schliefe.

    Die Leiter ist ``base * 2**(n-1)``, der Jitter multipliziert mit
    ``[1 - spread, 1 + spread]``. Die Untergrenze nimmt den kleinsten Faktor —
    unter diesen Wert kommt kein Durchgang, wie der Zufall auch faellt.
    """
    stufen = sum(2**n for n in range(api_client.METADATA_MAX_ATTEMPTS - 1))
    return api_client.METADATA_BACKOFF_BASE * stufen * (1.0 - api_client.METADATA_JITTER_SPREAD)


async def test_die_fixture_nullt_die_wartezeit():
    """Die Naht selbst: ``_sleep`` kostet keine Zeit mehr.

    Faellt, sobald die autouse-Fixture entfernt oder wirkungslos wird — dann
    dauert dieser Aufruf seine vollen ``_SPUERBAR`` Sekunden.
    """
    started = time.monotonic()
    await api_client._sleep(_SPUERBAR)
    verstrichen = time.monotonic() - started
    assert verstrichen < _SPUERBAR / 4, (
        f"`api_client._sleep` hat {verstrichen:.2f} s wirklich gewartet — die "
        "autouse-Fixture `_no_backoff` greift nicht mehr."
    )


async def test_der_erschoepfte_retry_pfad_kostet_keine_echte_zeit(monkeypatch):
    """Und die Wirkung dort, wo sie zaehlt: im Retry-Pfad des Aufrufs.

    Drei Versuche mit der Leiter 1 s / 2 s schlafen real mindestens 1.5 s. Bleibt
    der Aufruf klar darunter, ist die Wartezeit genullt — und zwar die, die der
    Code tatsaechlich nimmt, nicht bloss die Funktion, die ihn dahin bringt.
    """
    untergrenze = _echte_wartezeit_untergrenze()
    if untergrenze < _SPUERBAR:
        pytest.skip(
            f"Backoff-Leiter zu kurz ({untergrenze:.2f} s), um echte von "
            "genullter Wartezeit zu trennen — diese Zusicherung waere nicht mehr "
            "widerlegbar und damit wertlos."
        )

    calls = _stub_safe_get(monkeypatch, [httpx.ReadTimeout("slow")])

    started = time.monotonic()
    result = await api_client.fetch_zhlex_metadata(SR)
    verstrichen = time.monotonic() - started

    # Ohne diese Zeile misst der Test womoeglich einen Pfad, der gar nicht
    # wiederholt hat — und «schnell» hiesse dann nur «nie geschlafen».
    assert len(calls) == api_client.METADATA_MAX_ATTEMPTS
    assert result["found"] is False
    assert verstrichen < untergrenze / 3, (
        f"Der Aufruf brauchte {verstrichen:.2f} s; ab {untergrenze:.2f} s waere "
        "real geschlafen worden. Die autouse-Fixture `_no_backoff` greift nicht mehr."
    )
