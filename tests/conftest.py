"""Geteilte Test-Fixtures.

Befüllt einen LawCache mit deterministischen Beispieldaten, ohne den
HuggingFace-Download auszulösen (Unit-Tests müssen offline laufen).
"""
from __future__ import annotations

import sqlite3

import pytest

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
                    law["uuid"], law["title"], law["short_desc"],
                    law["abbreviation"], law["sr_number"], law["is_active"],
                    "", "", law["pdf_content"], law["html_content"],
                    "", "", "zh", "de",
                ),
            )
            conn.execute(
                """INSERT INTO laws_fts
                (uuid, title, short_desc, abbreviation, sr_number, body)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    law["uuid"], law["title"], law["short_desc"],
                    law["abbreviation"], law["sr_number"], law["pdf_content"],
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
