#!/usr/bin/env python3
"""Misst den Stand des Gesetzesbestands — und die Grenzen der eigenen Messung.

    python scripts/record_fixtures.py

WARUM ES DAS GIBT. Ein handgeschriebener Mock kodiert die Annahme seines
Autors und kann sie deshalb prinzipiell nicht widerlegen: Produktivcode und
Fixture stammen aus demselben Kopf, derselben Stunde, derselben Lektuere der
Doku. Wo beide irren, irren beide gleich, und die Suite bleibt gruen.

Dieser Server ist der gesuendeste des Portfolios: acht Werkzeuge, acht
Live-Tests, und sieben davon liefen. Der Befund liegt woanders — nicht darin,
WOHER die Antwort kommt, sondern WIE ALT sie ist.

WAS DER ERSTE VERGLEICH AM 2026-08-08 ERGAB.

1. **Der Bestand ist eingefroren.** Die juengste Fassung im gesamten Datensatz
   traegt `version_active_since = 2023-01-01`; der HuggingFace-Datensatz wurde
   zuletzt am 2024-10-10 angefasst. Der Cache gilt derweil 24 Stunden, und
   `provenance="cache"` liest sich wie «aus dem Zwischenspeicher». Beides sagt
   nichts ueber das Alter der Gesetze.

2. **Der Docstring von `zhlaw_update_cache` legte die falsche Wirkung nahe:**
   «Nur aufrufen wenn Gesetzes-Suchergebnisse veraltet wirken». Ein Update
   laedt denselben eingefrorenen Stand erneut herunter.

3. **Alle 974 Eintraege sind `is_active = True`, keiner traegt ein
   `version_inactive_since`.** Das ist KEIN Fehler — die Quelle fuehrt
   ausschliesslich die zum Aufnahmezeitpunkt gueltigen Erlasse. Es heisst
   aber: Ein spaeter aufgehobenes Gesetz erscheint weiterhin als in Kraft.
   Dieser Nullbefund gehoert aufgezeichnet, sonst wird er beim naechsten Mal
   erneut als Fehler vermutet.

WAS HIER AUSDRUECKLICH NICHT GEMESSEN WERDEN KONNTE. Die Live-Metadaten von
`zh.ch` bzw. `zhlex.zh.ch`. Das oeffentliche DNS fuehrt beide Namen
(194.247.8.174, gegengeprueft mit einer NXDOMAIN-Kontrolle) — die Hosts
existieren also. Erreichbar waren sie aus der Aufzeichnungsumgebung nicht.
Daraus folgt NICHTS ueber den Server: Eine Zustellgrenze der eigenen Umgebung
ist keine Aussage ueber die Quelle. `PROVENANCE.md` fuehrt das als offen.

Ohne Aufzeichnungsdatum ist «gemessen» nach zwei Jahren von «angenommen» nicht
mehr zu unterscheiden.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "src"))

# Alles aus dem Produktivcode. Ein Skript, das einen anderen Datensatz misst
# als der Server laedt, misst den falschen Gegenstand.
from openlex_mcp import data_cache  # noqa: E402
from openlex_mcp.responses import BESTAND_STAND  # noqa: E402

HF_API = "https://huggingface.co/api/datasets"
DOH = "https://cloudflare-dns.com/dns-query"

# Hosts, die der Server fuer Live-Metadaten baut — samt einer Kontrolle.
LIVE_HOSTS = [
    ("www.zh.ch", "Metadatenseite, von `fetch_zhlex_metadata` gebaut"),
    ("zhlex.zh.ch", "Permalink-Basis, von `build_zhlex_permalink` gebaut"),
    ("www.lexfind.ch", "Suchlink, von `build_lexfind_url` gebaut"),
    ("diesen-host-gibt-es-sicher-nicht.zh.ch", "KONTROLLE: erfundener Name"),
]


def record() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(UTC).strftime("%Y-%m-%d")
    entries: list[dict] = []

    def write(name: str, payload: object, url: str, rule: str) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        (FIXTURES / name).write_text(text, encoding="utf-8")
        entries.append(
            {
                "name": name,
                "url": url,
                "rule": rule,
                "bytes": len(text.encode("utf-8")),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
        print(f"ok  {name:<26} {len(text.encode('utf-8')):>7} B")

    # -- 1) Der Stand des Bestands, aus dem Cache des Servers ----------------
    db = data_cache.DEFAULT_DB_DIR / data_cache.DB_FILENAME
    if not db.is_file():
        raise SystemExit(
            f"Kein Cache unter {db}. Erst den Server einmal starten oder "
            "`zhlaw_update_cache` aufrufen, dann erneut aufzeichnen."
        )
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    gesamt = con.execute("SELECT COUNT(*) AS n FROM laws").fetchone()["n"]
    juengste = con.execute(
        "SELECT MAX(version_since) AS m FROM laws WHERE version_since != ''"
    ).fetchone()["m"]
    aktiv = con.execute("SELECT is_active, COUNT(*) AS n FROM laws GROUP BY is_active").fetchall()
    verteilung = {str(r["is_active"]): r["n"] for r in aktiv}
    con.close()

    juengstes_datum = (juengste or "")[:10]
    if juengstes_datum != BESTAND_STAND:
        raise SystemExit(
            f"Der Bestand reicht jetzt bis {juengstes_datum}, `BESTAND_STAND` "
            f"sagt {BESTAND_STAND}. Das ist eine gute Nachricht — die Konstante "
            "und die Hinweise in README und CHANGELOG gehoeren nachgezogen, "
            "nicht diese Pruefung."
        )
    if verteilung.get("0"):
        raise SystemExit(
            f"{verteilung['0']} Eintraege sind jetzt inaktiv. Bisher war "
            "ausnahmslos alles aktiv, weil die Quelle nur gueltige Erlasse "
            "fuehrt — der Hinweis auf aufgehobene Gesetze gehoert neu gefasst."
        )

    with httpx.Client(timeout=90.0, follow_redirects=True) as c:
        r = c.get(f"{HF_API}/{data_cache.HF_DATASET}")
        r.raise_for_status()
        hf = r.json()

        write(
            "bestand_stand.json",
            {
                "recorded_at": recorded_at,
                "datensatz": data_cache.HF_DATASET,
                "hf_last_modified": hf.get("lastModified"),
                "gesetze_im_cache": gesamt,
                "juengste_fassung": juengstes_datum,
                "is_active_verteilung": verteilung,
                "warum": (
                    "Der Cache gilt 24 Stunden — der Bestand darin ist Jahre "
                    "alt. Genau diese Verwechslung stand in der Antwort: "
                    "`provenance=cache` sagt, WOHER sie kam, nicht WIE ALT sie "
                    "ist"
                ),
            },
            f"{HF_API}/{data_cache.HF_DATASET} + lokaler Cache",
            "der Stand des Bestands, nicht der des Caches: juengste Fassung, "
            "Aenderungsdatum des Datensatzes und die Verteilung von "
            "`is_active`. Die letzte Zahl ist ein Nullbefund und steht "
            "deshalb hier — ohne sie wird beim naechsten Mal erneut ein "
            "Fehler vermutet, wo die Quelle schlicht nur gueltige Erlasse "
            "fuehrt",
        )

        # -- 2) Die Hosts der Live-Metadaten, ueber oeffentliches DNS --------
        #
        # Aus der Aufzeichnungsumgebung sind sie moeglicherweise nicht
        # erreichbar. Das waere eine Aussage ueber diese Umgebung und keine
        # ueber die Quelle — deshalb wird hier das oeffentliche DNS befragt
        # und nicht der eigene Netzpfad.
        hosts: dict[str, dict] = {}
        for name, warum in LIVE_HOSTS:
            d = c.get(
                DOH, params={"name": name, "type": "A"}, headers={"Accept": "application/dns-json"}
            ).json()
            hosts[name] = {
                "dns_status": d.get("Status"),
                "dns_label": {0: "NOERROR", 3: "NXDOMAIN"}.get(d.get("Status"), "?"),
                "adressen": [a.get("data") for a in d.get("Answer", [])][:3],
                "warum": warum,
            }
            print(f"    {hosts[name]['dns_label']:<9} {name}")

        if hosts["diesen-host-gibt-es-sicher-nicht.zh.ch"]["dns_label"] != "NXDOMAIN":
            raise SystemExit(
                "Der erfundene Hostname loest auf — dann unterscheidet diese "
                "Messung nicht, und sie belegt nichts."
            )
        tot = sorted(
            n for n, v in hosts.items() if v["dns_label"] != "NOERROR" and "nicht" not in n
        )
        if tot:
            raise SystemExit(
                f"Diese Hosts loesen nicht mehr auf: {tot}. Das gehoert "
                "geprueft — die Kontrolle zeigt, dass die Abfrage funktioniert."
            )
        write(
            "live_hosts_dns.json",
            {"recorded_at": recorded_at, "hosts": hosts},
            DOH,
            "die Hosts der Live-Metadaten ueber oeffentliches DNS-over-HTTPS, "
            "samt einer NXDOMAIN-Kontrolle. Bewusst NICHT ueber den eigenen "
            "Netzpfad: Aus der Aufzeichnungsumgebung waren zh.ch und "
            "zhlex.zh.ch nicht erreichbar, und daraus folgt nichts ueber die "
            "Quelle. Eine Zustellgrenze der eigenen Umgebung ist keine "
            "Aussage ueber den Bestand — dieser Unterschied ist im Portfolio "
            "schon mehrfach verwechselt worden",
        )

    _write_provenance(recorded_at, entries)
    print(f"\nPROVENANCE.md geschrieben, Aufzeichnungsdatum {recorded_at}")
    return 0


def _write_provenance(recorded_at: str, entries: list[dict]) -> None:
    lines = [
        "# Herkunft der Fixtures",
        "",
        "**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**",
        "",
        f"Aufgezeichnet am **{recorded_at}**.",
        "",
        "Ohne Datum ist «gemessen» nach zwei Jahren von «angenommen» nicht mehr",
        "zu unterscheiden — die Datei sieht gleich aus.",
        "",
        "## Aufgezeichnet ist der Stand des Bestands",
        "",
        "Dieser Server liefert aus einem lokalen Cache, und der Cache gilt 24",
        "Stunden. Der **Bestand** darin ist Jahre alt: Die juengste Fassung",
        'traegt `version_active_since = 2023-01-01`. `provenance="cache"` sagt,',
        "woher eine Antwort kam — nicht, wie alt die Gesetze darin sind. Genau",
        "diese beiden Fragen wurden verwechselt.",
        "",
        "Der Nullbefund gehoert dazu: Alle Eintraege sind `is_active = True`,",
        "keiner traegt ein `version_inactive_since`. Das ist kein Fehler des",
        "Servers, sondern die Form der Quelle — sie fuehrt nur gueltige",
        "Erlasse. Ohne diese Zeile wird beim naechsten Durchgang erneut ein",
        "Fehler vermutet, wo keiner ist.",
        "",
        "## NICHT gemessen: die Live-Metadaten",
        "",
        "`zhlaw_get_law_metadata` fragt `www.zh.ch` ab. Aus der",
        "Aufzeichnungsumgebung war der Host nicht erreichbar. **Daraus folgt",
        "nichts.** Das oeffentliche DNS fuehrt ihn (NOERROR, 194.247.8.174),",
        "und die NXDOMAIN-Kontrolle zeigt, dass die Abfrage unterscheidet — die",
        "Grenze liegt also bei der Aufzeichnungsumgebung, nicht bei der Quelle.",
        "",
        "Der entsprechende Live-Test ist deshalb **nicht** angepasst worden.",
        "Ein Test, den man rot sieht, weil die eigene Umgebung nicht",
        "hinauskommt, gehoert nicht umgeschrieben — sonst misst er danach die",
        "Umgebung statt die Quelle.",
        "",
    ]
    for e in entries:
        lines += [
            f"## `{e['name']}`",
            "",
            f"- **Quelle:** `{e['url']}`",
            f"- **Aufgezeichnet:** {recorded_at}",
            f"- **Auswahl:** {e['rule']}",
            f"- **Groesse:** {e['bytes']} B",
            f"- **SHA-256:** `{e['sha256']}`",
            "",
        ]
    (FIXTURES / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(record())
    except httpx.HTTPError as exc:
        print(f"FEHLER: Quelle nicht erreichbar: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
