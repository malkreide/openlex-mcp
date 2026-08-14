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
pip install -e ".[dev]"                       # enthält den ruff-Pin, siehe unten
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

### Der ruff-Pin steht in `pyproject.toml`

Und nur dort — `[project.optional-dependencies].dev` sagt `ruff==0.16.1`, die
CI installiert ihn über `pip install -e ".[dev]"` mit. Keinen zweiten Pin in
einen Workflow schreiben: Vorher stand `ruff==0.16.1` allein in `ci.yml`,
während `pyproject.toml` `ruff>=0.4.0` sagte — eine frische venv zog damit
0.16.3, die CI überschrieb sie mit 0.16.1. `tests/test_toolchain_pin.py` lässt
beide Hälften dieser Drift auflaufen. Bump gehört in einen eigenen Commit,
samt der Formatierungen, die er auslöst.

`.pre-commit-config.yaml` existiert nicht.

### Backoff in Tests

Die autouse-Fixture `_no_backoff` in `tests/conftest.py` nullt die Wartezeit
über den Alias `api_client._sleep`. Einzeltests patchen das **nicht** noch
einmal selbst. Sie hält Tests schnell (4.97 s → 0.60 s in
`test_api_client.py`) und ist keine Zusicherung: Wer sie neutralisiert, sieht
alle Tests grün bleiben, nur langsamer. Was sie absichert, ist die Naht —
`monkeypatch.setattr` fällt laut, sobald der Alias umbenannt wird, und
`test_die_fixture_laesst_das_echte_asyncio_sleep_in_ruhe` bewacht, dass nicht
doch `asyncio.sleep` selbst getroffen wird.
