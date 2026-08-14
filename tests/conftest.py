"""Geteilte Test-Fixtures.

Befüllt einen LawCache mit deterministischen Beispieldaten, ohne den
HuggingFace-Download auszulösen (Unit-Tests müssen offline laufen).
"""

from __future__ import annotations

import sqlite3
import time

import pytest

from openlex_mcp import api_client
from openlex_mcp.data_cache import LawCache

# Deterministische Beispielgesetze für Unit-Tests.
SAMPLE_LAWS: list[dict] = [
    {
        "uuid": "u-vsg",
        "title": "Volksschulgesetz",
        "short_desc": "Regelt die Volksschule im Kanton Zürich.",
        "abbreviation": "VSG",
        "sr_number": "412.100",
        "is_active": 1,
        "pdf_content": (
            "Art. 1 Zweck\n"
            "Dieses Gesetz regelt die Volksschule.\n\n"
            "Art. 28 Elternmitwirkung\n"
            "Die Eltern wirken bei der Schule mit. "
            "Ein Elternrat kann gebildet werden."
        ),
        "html_content": "",
    },
    {
        "uuid": "u-kv",
        "title": "Kantonsverfassung",
        "short_desc": "Verfassung des Kantons Zürich.",
        "abbreviation": "KV",
        "sr_number": "101.0",
        "is_active": 1,
        "pdf_content": "Art. 1 Grundlagen\nDer Kanton Zürich ist ein Freistaat.",
        "html_content": "",
    },
    {
        "uuid": "u-old",
        "title": "Aufgehobenes Gesetz",
        "short_desc": "",
        "abbreviation": "AG",
        "sr_number": "999.9",
        "is_active": 0,
        "pdf_content": "Art. 1 Dieses Gesetz wurde aufgehoben.",
        "html_content": "",
    },
]


def populate(cache: LawCache, laws: list[dict] | None = None) -> None:
    """Schreibt Beispielgesetze direkt in die `laws`- und `laws_fts`-Tabellen."""
    laws = laws if laws is not None else SAMPLE_LAWS
    conn = sqlite3.connect(str(cache.db_path))
    try:
        for law in laws:
            conn.execute(
                """INSERT OR REPLACE INTO laws
                (uuid, title, short_desc, abbreviation, sr_number, is_active,
                 pdf_url, html_url, pdf_content, html_content,
                 version_since, family_since, canton, language)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    law["uuid"],
                    law["title"],
                    law["short_desc"],
                    law["abbreviation"],
                    law["sr_number"],
                    law["is_active"],
                    "",
                    "",
                    law["pdf_content"],
                    law["html_content"],
                    "",
                    "",
                    "zh",
                    "de",
                ),
            )
            conn.execute(
                """INSERT INTO laws_fts
                (uuid, title, short_desc, abbreviation, sr_number, body)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    law["uuid"],
                    law["title"],
                    law["short_desc"],
                    law["abbreviation"],
                    law["sr_number"],
                    law["pdf_content"],
                ),
            )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _reset_shared_http_client():
    """Setzt den prozessweiten httpx-Client zwischen Tests zurück (SDK-001)."""
    import openlex_mcp.api_client as ac

    ac._client = None
    yield
    ac._client = None


@pytest.fixture
def cache(tmp_path) -> LawCache:
    """Ein befüllter LawCache in einem temporären Verzeichnis."""
    c = LawCache(db_dir=tmp_path)
    populate(c)
    return c


@pytest.fixture
def server_with_cache(cache, monkeypatch):
    """Das server-Modul, dessen globaler Cache auf den Test-Cache zeigt."""
    import openlex_mcp.server as srv

    monkeypatch.setattr(srv, "_cache", cache)
    return srv


@pytest.fixture(autouse=True)
def _no_backoff(monkeypatch):
    """Nullt die Wartezeit, ohne ``asyncio.sleep`` prozessweit stillzulegen.

    Gepatcht wird ``api_client._sleep``. Ein
    ``monkeypatch.setattr(api_client.asyncio, "sleep", ...)`` sähe lokal aus
    und trifft das stdlib-Modul — jeder Test, der ``asyncio.sleep`` benutzt, um
    dem Event-Loop das Wort zu geben, misst danach nichts mehr und bleibt grün.
    ``test_die_fixture_laesst_das_echte_asyncio_sleep_in_ruhe`` bewacht die Naht.
    """

    async def _instant(_seconds: float) -> None:
        return None

    monkeypatch.setattr(api_client, "_sleep", _instant)


def _mark_fresh(cache: LawCache, age_hours: float = 0.0) -> None:
    """Setzt ``cache_meta.last_update``, damit ``is_fresh()`` greift.

    ``populate()`` schreibt nur ``laws`` und ``laws_fts`` — den Zeitstempel
    nicht. Ein so befuellter Cache gilt deshalb als veraltet, und ein
    ``load_from_huggingface(force=False)`` darauf laedt wirklich herunter.
    """
    conn = sqlite3.connect(str(cache.db_path))
    try:
        conn.execute(
            "INSERT OR REPLACE INTO cache_meta (key, value) VALUES ('last_update', ?)",
            (str(int(time.time() - age_hours * 3600)),),
        )
        conn.commit()
    finally:
        conn.close()


class _NetzImUnitLauf(BaseException):
    """Der Wachhund schlaegt an — und zwar so, dass es niemand wegfaengt.

    Abgeleitet von ``BaseException`` und nicht von ``Exception``, weil
    ``load_from_huggingface`` seinen Download in ein ``except Exception``
    huellt: Ein gewoehnlicher Fehler wuerde dort zu ``status="error"`` und
    verschwaende in einer Log-Zeile. Ein Test mit schwacher Zusicherung bliebe
    dann gruen — genau die Lage, die diesen Wachhund noetig gemacht hat.
    """


@pytest.fixture
def mark_fresh():
    """Reicht ``_mark_fresh`` als Fixture durch — ``tests/`` ist kein Paket,
    ein ``from tests.conftest import ...`` scheitert deshalb beim Sammeln."""
    return _mark_fresh


@pytest.fixture(autouse=True)
def _kein_datensatz_download_im_unit_lauf(request, monkeypatch):
    """Laesst einen echten HuggingFace-Download im Unit-Lauf auflaufen.

    Die Zusage steht seit jeher im Kopf dieser Datei — «Unit-Tests muessen
    offline laufen» — nur konnte sie nichts durchsetzen. Ein Test hat sie
    gebrochen und dabei ~970 Gesetze wirklich geladen: 12-15 s pro Matrix-Job,
    in einem Lauf, der `-m "not live"` heisst. Aufgefallen ist es nur an der
    Laufzeit, denn die Zusicherung des Tests nahm jeden Status an, auch
    ``error`` — mit und ohne Netz blieb er gruen.

    Der Patch trifft hier bewusst das fremde Modul, anders als bei
    ``_no_backoff``: Ihn lokal zu halten waere gerade falsch, denn genau das
    prozessweite Stillegen ist die Zusage. Und kein Unit-Test misst
    ``load_dataset`` — wer es ruft, will herunterladen.

    Live-Tests sind ausgenommen; sie duerfen und sollen an die Quelle.
    """
    if request.node.get_closest_marker("live"):
        return

    import datasets

    def _verboten(*_args, **_kwargs):
        raise _NetzImUnitLauf(
            'load_dataset() in einem Unit-Test — der Lauf `-m "not live"` geht '
            "damit ans Netz und dauert je nach Bandbreite Sekunden bis Minuten. "
            "Den Aufruf stubben, oder den Cache mit `mark_fresh()` als frisch "
            "markieren. Gehoert der Test wirklich an die Quelle, dann mit "
            "`@pytest.mark.live` in tests/test_live.py."
        )

    monkeypatch.setattr(datasets, "load_dataset", _verboten)
