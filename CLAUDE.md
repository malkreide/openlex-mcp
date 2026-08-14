# CLAUDE.md

## Teil 1 — Portfolio-Konventionen

### Vor der Arbeit

Klon-Aktualität prüfen: `git fetch origin main && git rev-list --count HEAD..origin/main`
Ein veralteter Klon erzeugt eine rote CI, deren Ursache nicht im Diff steht.
Am 3.8.2026 zweimal passiert — beide Male fehlten genau die Commits, die
das Gate einführten, an dem der Branch scheiterte.

Gates lokal fahren, mit der GEPINNTEN ruff-Version aus der CI. Eine andere
Version meldet Abweichungen, die niemand verursacht hat.

### Tests

Gegenprobe ist Pflicht. Ein Test, der grün bleibt, wenn man die
Implementierung entfernt, prüft nichts. Jede neue Zusicherung einzeln
neutralisieren und zeigen, dass genau die zugehörigen Tests fallen.

Zwei Fallen, die beide grün blieben:

- Eine Fake-Uhr, die nur beim Schlafen vorrückt, kann eine Zusicherung über
  echte Zeit nicht widerlegen.
- `monkeypatch.setattr(modul.asyncio, "sleep", ...)` greift ins Modul
  `asyncio` selbst und entschärft die Mechanik im ganzen Prozess. Patche
  einen Modul-Alias (`_sleep = asyncio.sleep`), nicht das fremde Modul.

Handgeschriebene Fixtures kodieren die Annahme des Autors und können sie
nicht widerlegen. Mindestens eine aufgezeichnete Antwort pro externem
Endpunkt, mit Aufnahmedatum.

### Wenn etwas rot ist

Roter Live-Test: erst die Quelle abfragen, dann einordnen. Nicht aus der
Fehlermeldung schliessen. Am 3.8.2026 hiess «nicht gefunden» nicht, dass der
Datensatz weg war, sondern dass die Quelle die Schreibweise ihrer Kopfzeile
gewechselt hatte — vier von sechs Datensätzen produktiv kaputt, alle
Unit-Tests grün.

PR ohne jeden Check ist selten ein Repo ohne CI, meistens ein
Merge-Konflikt: GitHub berechnet dafür keinen Merge-Commit und startet nichts.

Ein Codex-Review auf einem PR wird beantwortet oder behoben, nie ignoriert.

## Teil 2 — Dieses Repo

Default-Branch ist `master` (CI triggert auf `[main, master]`). Der Befehl
oben lautet hier `git fetch origin master && git rev-list --count HEAD..origin/master`.

### Gates, wörtlich aus `.github/workflows/ci.yml`

```
pip install ruff==0.16.1                      # Pin NUR in der CI, siehe Befund
PYTHONPATH=src pytest tests/ -m "not live"
ruff check src/ tests/ scripts/
ruff format --check src/ tests/ scripts/
python scripts/check_version_sync.py
```

Matrix: Python 3.11 / 3.12 / 3.13.

### Live-Tests

Geplanter Workflow vorhanden: `.github/workflows/live.yml`, cron `0 4 * * *`
(04:00 UTC) plus `workflow_dispatch`, Befehl `PYTHONPATH=src pytest -m live -v`.
DRIFT-005 ist damit erfüllt — Live-Tests sind nicht bloss per `-m "not live"`
ausgeschlossen. Fixture-Provenienz: `tests/fixtures/PROVENANCE.md`,
aufgezeichnet 2026-08-08, erzeugt von `scripts/record_fixtures.py`.

### Befunde

1. **ruff-Pin nur in der CI.** `.pre-commit-config.yaml` existiert nicht. Die
   einzige zweite Deklaration ist `ruff>=0.4.0` in `pyproject.toml`
   (`[project.optional-dependencies].dev`) — offen nach oben und damit **nicht**
   deckungsgleich mit dem CI-Pin `0.16.1`. `pip install -e ".[dev]"` zieht lokal
   die jeweils neuste ruff; die CI überschreibt sie danach mit 0.16.1. Lokale
   Gates deshalb explizit mit `ruff==0.16.1` fahren, bis der Pin an einer
   gemeinsamen Stelle steht.
2. **Die Falle aus Teil 1 ist im Repo aktiv.** `tests/test_api_client.py`
   patcht an drei Stellen `api_client.asyncio, "sleep"` (Z. 128, 146, 164) und
   legt damit `asyncio.sleep` prozessweit still. `tests/conftest.py` macht es
   richtig über den Alias `api_client._sleep`, und
   `test_die_fixture_laesst_das_echte_asyncio_sleep_in_ruhe` bewacht genau
   diese Naht. Die drei Stellen auf die Fixture umstellen.
