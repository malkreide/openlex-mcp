"""SEC-022: Der Hash-Schnappschuss ist jetzt ein Gate, keine Konvention mehr.

`scripts/gen_tool_hashes.py` gab es schon, aber **nichts prüfte ihn** — kein
CI-Schritt, kein Test. Die Anweisung stand allein in der README, als Handgriff
beim Ändern der Protokollversion. Ein vergessenes Nachziehen fiel entsprechend
nirgends auf, und genau das ist passiert: der Schnappschuss war acht Hashes weit
veraltet, ohne dass ein einziger Lauf rot wurde.

Ein Schnappschuss, den niemand vergleicht, schützt vor nichts. Er sieht nur so
aus.
"""

from __future__ import annotations

import asyncio
import json
import pathlib

import pytest

from openlex_mcp.server import MCP_PROTOCOL_VERSION

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SNAPSHOT = _ROOT / "docs" / "tool-hashes.json"


def _skript():
    """Lädt `scripts/gen_tool_hashes.py` als Modul.

    Über den Dateipfad statt über einen Import: `scripts/` ist kein Paket, und
    der Test soll genau das Skript fahren, das auch von Hand aufgerufen wird —
    eine nachgebaute Kopie der Hash-Funktion könnte sich davon fortbewegen, ohne
    dass es auffällt.
    """
    import importlib.util

    pfad = _ROOT / "scripts" / "gen_tool_hashes.py"
    spec = importlib.util.spec_from_file_location("gen_tool_hashes", pfad)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def aktuell() -> dict[str, str]:
    return asyncio.run(_skript().current_hashes())


@pytest.fixture(scope="module")
def schnappschuss() -> dict:
    return json.loads(_SNAPSHOT.read_text(encoding="utf-8"))


def test_kein_werkzeug_ist_dazugekommen_oder_entfallen(aktuell, schnappschuss) -> None:
    """Die grobe Hälfte: ein zusätzliches Werkzeug ist die auffälligste Form
    eines Rug-Pulls und zugleich die, die man beim Lesen eines Diffs übersieht."""
    assert set(aktuell) == set(schnappschuss["tools"]), (
        f"neu: {sorted(set(aktuell) - set(schnappschuss['tools']))}, "
        f"entfallen: {sorted(set(schnappschuss['tools']) - set(aktuell))}"
    )


def test_keine_werkzeug_definition_hat_sich_still_geaendert(aktuell, schnappschuss) -> None:
    """Name, Beschreibung, Eingabe- und Ausgabeschema — das, was ein Client sieht.

    Eine gewollte Änderung wird im selben PR bestätigt:
    `python scripts/gen_tool_hashes.py --write`.
    """
    alt = schnappschuss["tools"]
    abweichend = sorted(n for n in set(alt) & set(aktuell) if alt[n] != aktuell[n])
    assert not abweichend, (
        f"Definition geändert: {abweichend}. War das gewollt, den Schnappschuss "
        "im selben PR neu schreiben (scripts/gen_tool_hashes.py --write)."
    )


def test_die_protokollversion_im_schnappschuss_stimmt(schnappschuss) -> None:
    """Das Feld war am 22.8. schon einmal einzeln nachgezogen worden, während
    die Hashes liegen blieben. Beides gehört zusammen geprüft."""
    assert schnappschuss["mcp_protocol_version"] == MCP_PROTOCOL_VERSION


def test_die_werkzeugzahl_im_schnappschuss_stimmt(aktuell, schnappschuss) -> None:
    assert schnappschuss["tool_count"] == len(aktuell) == len(schnappschuss["tools"])


def test_der_hash_ist_unabhaengig_vom_docstring_einzug() -> None:
    """Python 3.13 dedentiert Docstrings beim Kompilieren, 3.11 nicht.

    Derselbe Quelltext liefert dort eine Beschreibung mit vier Leerzeichen
    Einzug auf jeder Folgezeile und hier eine ohne. Gemessen an diesem Server:
    **null von acht** Hashes stimmten zwischen 3.11 und 3.13 überein, während
    Eingabe- und Ausgabeschema Zeichen für Zeichen identisch waren.

    Aufgefallen ist das nicht lokal — der Container fährt 3.11 —, sondern in der
    CI-Matrix, die zusätzlich 3.12 und 3.13 fährt. Ein Schnappschuss, der auf
    einem Feld immer rot ist, wäre schlimmer als keiner: er wird abgeschaltet.

    Normalisiert wird ausschliesslich der Einzug. Der zweite Fall unten zeigt,
    dass eine echte Umformulierung den Hash weiterhin ändert.
    """
    skript = _skript()

    class Attrappe:
        def __init__(self, description):
            self.name = "x"
            self.description = description
            self.input_schema = {"type": "object"}
            self.output_schema = None

    wie_311 = "Erste Zeile.\n\n    Zweite Zeile mit Einzug.\n    Dritte Zeile."
    wie_313 = "Erste Zeile.\n\nZweite Zeile mit Einzug.\nDritte Zeile."
    assert skript._tool_hash(Attrappe(wie_311)) == skript._tool_hash(Attrappe(wie_313))

    # Gegenkontrolle: normalisiert wird der Einzug, nicht der Inhalt.
    umformuliert = "Erste Zeile.\n\nZweite Zeile mit Einzug.\nVierte Zeile."
    assert skript._tool_hash(Attrappe(wie_313)) != skript._tool_hash(Attrappe(umformuliert))


def test_der_hash_liest_den_vertrag_und_nicht_die_sdk_interna(aktuell) -> None:
    """Warum die Nutzlast auf `inputSchema`/`outputSchema` steht.

    Die frühere Fassung hashte `mcp._tool_manager._tools` und dort das Attribut
    `parameters`. Dasselbe Werkzeug hat über die öffentliche Liste gar kein
    `parameters`, sondern `input_schema` — es sind zwei verschiedene Objekte.
    Als die 2.x-Migration die Interna umbaute, änderten sich deshalb alle acht
    Hashes, obwohl seit der letzten Erzeugung kein Commit `server.py` angefasst
    hatte.

    Dieser Test hält fest, dass der Schnappschuss an der öffentlichen Liste
    hängt: verschwände sie oder verlöre ein Werkzeug sein Eingabeschema, wäre
    das ein echter Vertragsbruch und kein Umbenennen.
    """
    skript = _skript()

    async def hole():
        from openlex_mcp.server import mcp

        return await mcp.list_tools()

    werkzeuge = asyncio.run(hole())
    assert werkzeuge, "die oeffentliche Werkzeugliste ist leer"
    for t in werkzeuge:
        assert isinstance(t.input_schema, dict) and t.input_schema, f"{t.name} ohne Eingabeschema"
        assert skript._tool_hash(t) == aktuell[t.name]
