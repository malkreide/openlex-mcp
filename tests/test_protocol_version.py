"""ARCH-012: der Protokoll-Pin muss die Revision nennen, die der Server spricht.

Die Konstante stand auf `2025-11-25`, waehrend das gepinnte SDK
(`mcp>=2.0.0,<3`) `2026-07-28` aushandelt. Aufgefallen ist das nicht, und der
Grund steht in `tests/test_server.py`: die einzige Zusicherung auf diesen Wert
prueft seine *Form* — zehn Zeichen, zwei Bindestriche. Ein veraltetes Datum
erfuellt das tadellos.

Eine Formpruefung kann eine Aussage ueber Inhalt nicht widerlegen. Hier steht
deshalb die Zusicherung, die gefehlt hat: der Pin gegen das, was das installierte
SDK tatsaechlich aushandelt.
"""

from __future__ import annotations

import pathlib
import re

from mcp.types import LATEST_PROTOCOL_VERSION

from openlex_mcp.server import MCP_PROTOCOL_VERSION

REPO = pathlib.Path(__file__).resolve().parents[1]


def test_der_pin_nennt_die_revision_des_installierten_sdk() -> None:
    """Faellt, wenn ein SDK-Update die Protokollversion verschiebt.

    Die Loesung ist dann nicht, die Konstante blind nachzuziehen: erst das
    Spec-Changelog lesen, das Serververhalten pruefen, dann Konstante, den
    README-Abschnitt und `CHANGELOG.md` in einem Commit anheben.
    """
    assert MCP_PROTOCOL_VERSION == LATEST_PROTOCOL_VERSION, (
        f"gepinnt {MCP_PROTOCOL_VERSION}, das SDK handelt {LATEST_PROTOCOL_VERSION} aus"
    )


def test_der_pin_ist_ein_datum_und_kein_bewegliches_ziel() -> None:
    """«latest» oder eine Range waeren keine Festlegung."""
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", MCP_PROTOCOL_VERSION), MCP_PROTOCOL_VERSION


def test_die_readme_nennt_dieselbe_revision() -> None:
    """Ein Pin, den die Doku anders angibt, ist zwei Angaben — und genau diese
    beiden waren auseinandergelaufen."""
    section = (
        (REPO / "README.md").read_text(encoding="utf-8").split("MCP Protocol Version", 1)[1][:800]
    )
    assert MCP_PROTOCOL_VERSION in section, (
        f"der Protokoll-Abschnitt der README nennt nicht {MCP_PROTOCOL_VERSION}"
    )


def test_die_readme_nennt_die_sdk_anforderung_aus_pyproject() -> None:
    """Dort stand `mcp[cli] >= 1.3.0 (FastMCP)` — eine Anforderung von vor der
    Migration auf `mcp` 2.x, dazu ein SDK-Name, den dieser Server nicht
    verwendet. Verglichen wird jetzt, statt darauf zu warten, dass jemand beide
    Dateien nebeneinanderlegt."""
    import tomllib

    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    requirement = next(d for d in data["project"]["dependencies"] if d.startswith("mcp"))
    section = (
        (REPO / "README.md").read_text(encoding="utf-8").split("MCP Protocol Version", 1)[1][:800]
    )
    assert requirement in section, (
        f"die README nennt nicht die deklarierte Anforderung `{requirement}`"
    )
