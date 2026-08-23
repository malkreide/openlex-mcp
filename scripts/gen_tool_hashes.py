#!/usr/bin/env python3
"""Hash-Schnappschuss der Tool-Definitionen (SEC-022, Rug-Pull-Schutz).

Bildet je Werkzeug einen SHA-256 ueber seinen *Vertrag* — Name, Beschreibung,
Eingabe- und Ausgabeschema — und vergleicht ihn mit dem eingecheckten
Schnappschuss `docs/tool-hashes.json`. Eine Abweichung heisst, dass sich die
beobachtbare Definition eines Werkzeugs geaendert hat. In der CI faellt der Lauf
dann, damit eine stille Aenderung dessen, was ein Werkzeug zu tun behauptet,
nicht unbemerkt ausgeliefert wird.

Eine beabsichtigte Aenderung wird durch Neuschreiben im selben PR bestaetigt
(`--write`) — dadurch steht sie als Diff im Review.

Aufruf:
    python scripts/gen_tool_hashes.py --check    # CI: faellt bei Abweichung
    python scripts/gen_tool_hashes.py --write    # nach gewollter Aenderung
    python scripts/gen_tool_hashes.py --print    # nur ausgeben

**Warum ueber `mcp.list_tools()` und nicht ueber `_tool_manager._tools`.** Die
frueheren Hashes lasen das interne Registrierungsobjekt und hashten dessen
Attribut `parameters`. Das ist nicht der Vertrag, sondern die SDK-interne
Buchhaltung: dasselbe Werkzeug liefert ueber die oeffentliche Liste ein Objekt
mit `input_schema`, und `parameters` gibt es dort gar nicht. Als die 2.x-Migration
die Interna umbaute, aenderten sich deshalb **alle acht** Hashes, obwohl seit der
letzten Erzeugung kein einziger Commit `server.py` angefasst hatte.

Die Nutzlast steht darum auf den *Wire*-Namen `inputSchema`/`outputSchema` —
der Schnappschuss bindet sich an das, was Clients ueber das Protokoll sehen,
nicht an die lokale Schreibweise des SDK. Dieselbe Loesung faehrt
`bag-health-mcp` im Portfolio.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import inspect
import json
import sys
from pathlib import Path

# Lauf aus dem Repo-Wurzelverzeichnis ohne Installation.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

SNAPSHOT = Path(__file__).resolve().parent.parent / "docs" / "tool-hashes.json"


def _tool_hash(tool) -> str:
    """Stabiler SHA-256 ueber den beobachtbaren Vertrag eines Werkzeugs.

    `inspect.cleandoc` statt `.strip()`: Python 3.13 dedentiert Docstrings beim
    Kompilieren, aeltere Versionen nicht. Derselbe Quelltext liefert dort also
    eine Beschreibung, deren Folgezeilen vier Leerzeichen Einzug tragen, und
    hier eine ohne — gemessen an 3.11 gegen 3.13: **null von acht** Hashes
    stimmten ueberein, waehrend Eingabe- und Ausgabeschema Zeichen fuer Zeichen
    identisch waren. Die CI-Matrix faehrt beide Versionen, ein roher Hash waere
    dort also auf einem Feld immer rot.

    Normalisiert wird nur der Einzug, den der Interpreter zufuegt oder wegnimmt.
    Eine echte Umformulierung aendert den Hash weiterhin — das ist der Zweck.
    """
    payload = {
        "name": tool.name,
        "description": inspect.cleandoc(tool.description or ""),
        "inputSchema": tool.input_schema,
        "outputSchema": getattr(tool, "output_schema", None),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


async def current_hashes() -> dict[str, str]:
    from openlex_mcp.server import mcp

    tools = await mcp.list_tools()
    return {t.name: _tool_hash(t) for t in sorted(tools, key=lambda t: t.name)}


def current_snapshot(hashes: dict[str, str]) -> dict:
    from openlex_mcp import server as srv

    return {
        "mcp_protocol_version": srv.MCP_PROTOCOL_VERSION,
        "tool_count": len(hashes),
        "tools": hashes,
    }


def load_snapshot() -> dict:
    if not SNAPSHOT.exists():
        return {}
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="SEC-022 Tool-Hash-Schnappschuss")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="bei Abweichung fehlschlagen (Standard)")
    g.add_argument("--write", action="store_true", help="Schnappschuss neu schreiben")
    g.add_argument("--print", action="store_true", help="aktuelle Hashes ausgeben")
    args = ap.parse_args()

    hashes = asyncio.run(current_hashes())
    neu = current_snapshot(hashes)

    if args.print:
        print(json.dumps(neu, indent=2, ensure_ascii=False))
        return 0

    if args.write:
        SNAPSHOT.write_text(json.dumps(neu, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{SNAPSHOT.relative_to(SNAPSHOT.parents[1])} geschrieben: {len(hashes)} Werkzeuge")
        return 0

    alt = load_snapshot()
    if not alt:
        print(f"Kein Schnappschuss unter {SNAPSHOT}. Mit --write anlegen.", file=sys.stderr)
        return 1

    fehler: list[str] = []
    if alt.get("mcp_protocol_version") != neu["mcp_protocol_version"]:
        fehler.append(
            f"Protokollversion: Schnappschuss {alt.get('mcp_protocol_version')!r}, "
            f"Server {neu['mcp_protocol_version']!r}"
        )
    a, n = alt.get("tools", {}), neu["tools"]
    for name in sorted(set(a) - set(n)):
        fehler.append(f"entfallen: {name}")
    for name in sorted(set(n) - set(a)):
        fehler.append(f"neu: {name}")
    for name in sorted(set(a) & set(n)):
        if a[name] != n[name]:
            fehler.append(f"Definition geaendert: {name}")

    if fehler:
        print("Tool-Hashes weichen vom Schnappschuss ab (SEC-022):", file=sys.stderr)
        for zeile in fehler:
            print(f"  - {zeile}", file=sys.stderr)
        print(
            "\nWar die Aenderung gewollt, im selben PR neu schreiben:\n"
            "    python scripts/gen_tool_hashes.py --write",
            file=sys.stderr,
        )
        return 1

    print(f"Tool-Hashes unveraendert: {len(n)} Werkzeuge, Protokoll {neu['mcp_protocol_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
