"""Wie alt die Gesetze sind — nicht, woher die Antwort kam.

Ohne Netz. Grundlage ist `tests/fixtures/`, aufgezeichnet am 2026-08-08 von
`scripts/record_fixtures.py`.

Dieser Server ist der gesuendeste des Portfolios: acht Werkzeuge, acht
Live-Tests. Der Befund liegt deshalb nicht in der Mechanik, sondern in einer
Verwechslung zweier Fragen, von denen bisher nur eine beantwortet wurde:

* `provenance="cache"` — **woher** diese Antwort kam.
* `corpus_as_of="2023-01-01"` — **wie alt** die Gesetze darin sind.

Wer «ist das aktuell?» fragt, meint die zweite.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from openlex_mcp.responses import BESTAND_HINWEIS, BESTAND_STAND, Envelope

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _fixture(name: str) -> dict:
    pfad = FIXTURES / name
    if not pfad.is_file():
        raise FileNotFoundError(
            f"Keine Fixture unter {pfad}. Neu aufzeichnen mit `python scripts/record_fixtures.py`."
        )
    return copy.deepcopy(json.loads(pfad.read_text(encoding="utf-8")))


class TestBestandsstand:
    def test_die_konstante_stimmt_mit_der_messung_ueberein(self):
        """Sonst ist `BESTAND_STAND` eine Behauptung statt einer Messung."""
        assert _fixture("bestand_stand.json")["juengste_fassung"] == BESTAND_STAND

    def test_der_bestand_ist_aelter_als_das_aenderungsdatum_des_datensatzes(self):
        """Die zwei Daten, die man nicht verwechseln darf.

        Der Datensatz wurde 2024-10-10 angefasst; die juengste Fassung darin
        stammt vom 2023-01-01. Selbst «der Datensatz ist von 2024» waere also
        noch zu optimistisch gewesen.
        """
        b = _fixture("bestand_stand.json")
        assert b["hf_last_modified"][:4] > b["juengste_fassung"][:4]

    def test_jede_antwort_traegt_den_bestandsstand(self):
        """Er steht im Envelope, nicht in einer Fussnote.

        Ein Hinweis, den man nur in der README findet, erreicht niemanden, der
        das Werkzeug ueber einen Assistenten benutzt.
        """
        e = Envelope(provenance="cache")
        assert e.corpus_as_of == BESTAND_STAND
        assert e.corpus_note == BESTAND_HINWEIS

    def test_der_hinweis_nennt_die_folge_und_nicht_nur_das_datum(self):
        """Ein Datum allein sagt einem Leser nichts.

        Die Folge ist das, was zaehlt: Ein nach dem Stichtag aufgehobenes
        Gesetz erscheint weiterhin als in Kraft.
        """
        assert "aufgehoben" in BESTAND_HINWEIS
        assert BESTAND_STAND in BESTAND_HINWEIS

    def test_alle_eintraege_sind_aktiv_und_das_ist_kein_fehler(self):
        """Der Nullbefund, festgehalten, damit er nicht neu vermutet wird.

        Die Quelle fuehrt ausschliesslich die zum Aufnahmezeitpunkt gueltigen
        Erlasse — kein Eintrag traegt ein `version_inactive_since`. `is_active`
        ist also nicht falsch berechnet, es ist schlicht ueberall wahr. Genau
        deshalb braucht es den Bestandsstand: Aufhebungen nach dem Stichtag
        sind unsichtbar.
        """
        v = _fixture("bestand_stand.json")["is_active_verteilung"]
        assert set(v) == {"1"}, f"Jetzt gibt es inaktive Eintraege: {v}"


class TestGrenzenDerEigenenMessung:
    """Was die Aufzeichnungsumgebung nicht messen konnte — und warum das nichts
    ueber die Quelle sagt."""

    def test_die_hosts_der_live_metadaten_existieren(self):
        """Aus der Aufzeichnungsumgebung waren sie nicht erreichbar.

        Daraus folgt nichts: Das oeffentliche DNS fuehrt sie. Ein Fehlschlag
        des eigenen Netzpfads ist keine Aussage ueber den Bestand der Quelle —
        diese Verwechslung ist im Portfolio schon mehrfach passiert, und sie
        haette hier zum Loeschen eines funktionierenden Werkzeugs gefuehrt.
        """
        h = _fixture("live_hosts_dns.json")["hosts"]
        for name in ("www.zh.ch", "zhlex.zh.ch", "www.lexfind.ch"):
            assert h[name]["dns_label"] == "NOERROR", f"{name}: {h[name]}"
            assert h[name]["adressen"], name

    def test_die_kontrolle_traegt_diese_aussage(self):
        """Ohne sie hiesse sie nur «ich habe eine Antwort bekommen»."""
        h = _fixture("live_hosts_dns.json")["hosts"]
        kontrolle = h["diesen-host-gibt-es-sicher-nicht.zh.ch"]
        assert kontrolle["dns_label"] == "NXDOMAIN"
        assert not kontrolle["adressen"]


class TestUpdateCacheVerspricht:
    """Der Docstring darf keine Wirkung mehr nahelegen, die es nicht gibt."""

    def test_kein_hinweis_mehr_auf_veraltete_suchergebnisse(self):
        """Hier stand «Nur aufrufen wenn Gesetzes-Suchergebnisse veraltet
        wirken» — genau die Wirkung, die dieses Werkzeug nicht hat.

        Es laedt denselben eingefrorenen Datensatz erneut herunter. Ein
        Assistent, der den Docstring liest, ruft es auf und meldet dem Nutzer
        danach dieselben Gesetze von 2023 als frisch geladen.
        """
        from openlex_mcp.server import zhlaw_update_cache

        doc = zhlaw_update_cache.__doc__ or ""
        assert "veraltet wirken" not in doc
        assert BESTAND_STAND in doc, (
            "Der Docstring muss den Bestandsstand nennen — sonst bleibt die "
            "Grenze dieses Werkzeugs unsichtbar."
        )
