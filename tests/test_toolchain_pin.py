"""Bewacht die Naht, an der die ruff-Version auseinanderlaufen kann.

Ein Lint- und Format-Gate sagt nur dann etwas zu, wenn lokal dieselbe Version
laeuft wie in der CI. Eine andere Version meldet Abweichungen, die niemand
verursacht hat — und zwar auf unberuehrtem Code, was die Suche nach der Ursache
in den Diff lenkt, wo sie nicht steht.

Genau das lag hier vor: `ci.yml` pinnte `ruff==0.16.1` in einem eigenen
Install-Schritt, waehrend `pyproject.toml` unter `[dev]` `ruff>=0.4.0` sagte.
Ein frisches `pip install -e ".[dev]"` zog damit die jeweils neuste ruff (beim
Befund 0.16.3), die CI ueberschrieb sie danach mit 0.16.1. Beide Deklarationen
waren fuer sich richtig; falsch war, dass es zwei gab.

Der Pin steht seither allein in `pyproject.toml`. Diese Tests halten das fest:
er muss exakt sein, und keine Workflow-Datei darf eine zweite, abweichende
Version einfuehren.

Bewusst nur Standardbibliothek und ohne Netz — der Test prueft Deklarationen,
nicht die installierte Umgebung. Was `pip` tatsaechlich aufloest, haengt am
Installationszeitpunkt; die CI wuerde davon flackernd rot.
"""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"
WORKFLOWS = ROOT / ".github" / "workflows"

# `ruff==0.16.1`, auch mit Leerzeichen um das `==`. Die Ziffer ist Absicht:
# Prosa wie «kein `pip install ruff==...`» soll nicht als Deklaration zaehlen.
_RUFF_PIN = re.compile(r"ruff\s*==\s*(\d[^\s'\",;\]]*)")


def _dev_requirements() -> list[str]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return data["project"]["optional-dependencies"]["dev"]


def _ruff_requirement() -> str:
    hits = [req for req in _dev_requirements() if re.match(r"\s*ruff\b", req)]
    assert len(hits) == 1, f"genau eine ruff-Zeile in [dev] erwartet, gefunden: {hits}"
    return hits[0]


def _pinned_version() -> str | None:
    """Die exakt gepinnte Version, oder ``None`` bei offenem Specifier."""
    match = _RUFF_PIN.fullmatch(_ruff_requirement().strip())
    return match.group(1) if match else None


def test_ruff_ist_in_pyproject_exakt_gepinnt():
    """Ein offener Specifier (`>=`) ist der Ausgangszustand des Befunds."""
    requirement = _ruff_requirement()
    assert _pinned_version() is not None, (
        f"ruff muss exakt gepinnt sein (`ruff==X.Y.Z`), steht aber als {requirement!r}. "
        "Ein nach oben offener Specifier laesst lokal und in der CI verschiedene "
        "Versionen zu — das Gate sagt dann nichts mehr zu."
    )


@pytest.mark.skipif(not WORKFLOWS.is_dir(), reason="keine Workflows im Repo")
def test_keine_workflow_datei_pinnt_ruff_abweichend():
    """Der Pin steht an genau einer Stelle — sonst beginnt dieselbe Drift von vorn.

    Eine Workflow-Datei darf ruff erwaehnen (`ruff check ...`), aber keine
    zweite Version festlegen. Taete sie es mit demselben Wert, waere sie beim
    naechsten Bump die Haelfte, die jemand vergisst.
    """
    pinned = _pinned_version()
    if pinned is None:
        # Ohne exakten Pin gibt es nichts zu vergleichen. Der fehlende Pin ist
        # der eigentliche Befund und faellt oben — hier waere er nur ein
        # zweiter, unspezifischer Fehlschlag (vorher: ein `AttributeError`,
        # der die Ursache verdeckte statt sie zu nennen).
        pytest.skip("kein exakter Pin in pyproject.toml — siehe Test oben")

    abweichungen = [
        (path.name, found)
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for found in _RUFF_PIN.findall(path.read_text(encoding="utf-8"))
        if found != pinned
    ]
    assert not abweichungen, (
        f"pyproject.toml pinnt ruff auf {pinned}, diese Workflows nennen eine andere "
        f"Version: {abweichungen}. Den Pin in pyproject.toml bumpen, nicht im Workflow."
    )
