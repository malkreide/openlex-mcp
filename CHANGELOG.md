# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Browser-Clients scheiterten am Preflight.** Spec `2026-07-28` routet eine
  Streamable-HTTP-Anfrage ueber `Mcp-Method`, `Mcp-Name` und
  `Mcp-Protocol-Version`. Die Freigabeliste nannte davon nur den letzten — und
  daneben `Mcp-Session-Id`, den Session-Header, der fuer sich genommen keine
  Anfrage routet. Ein Browser darf einen nicht safelisteten Header nicht
  senden, wenn der Server ihn nicht nennt: die Anfrage starb vor dem ersten
  MCP-Byte, waehrend stdio und Python weiterliefen.

- **Der Protokoll-Pin nannte `2025-11-25`,** waehrend das gepinnte SDK
  `2026-07-28` aushandelt. Aufgefallen ist es nicht, weil die einzige
  Zusicherung auf diesen Wert seine Form prueft — zehn Zeichen, zwei
  Bindestriche, was ein veraltetes Datum tadellos erfuellt.
  `tests/test_protocol_version.py` haelt den Pin jetzt gegen
  `LATEST_PROTOCOL_VERSION` aus dem SDK.

- **Der Protokoll-Abschnitt der README nannte `mcp[cli] >= 1.3.0 (FastMCP)`** —
  eine Anforderung von vor der Migration auf `mcp` 2.x, dazu ein SDK-Name, den
  dieser Server nicht verwendet. `pyproject.toml` bindet auf
  `mcp[cli]>=2.0.0,<3`.

### Added

- **Frischehinweise auf `tools/list` und `server/discover`** (SEP-2549, Spec
  `2026-07-28`): `ttlMs` 300000, `cacheScope` `public`. Das SDK setzt sonst
  «sofort veraltet, nie geteilt» und laesst damit jeden Client bei jeder
  Verbindung neu auflisten — fuer eine Liste, die beim Import feststeht.
  `prompts/list` und `resources/list` bleiben ungesetzt: dieser Server
  registriert weder das eine noch das andere.

- **Der Protokoll-Pin sicherte nur eine der beiden Spec-Aeren.** `mcp` 2.x
  bedient zwei ueber denselben Server; die erste Anfrage einer Verbindung
  entscheidet, welche gilt: der `initialize`-Handshake deckelt bei
  `2025-11-25`, der Pro-Request-Envelope erreicht `2026-07-28`.

  Die bisherige Zusicherung lautete `PIN == LATEST_PROTOCOL_VERSION` und las
  sich vollstaendig. `LATEST_PROTOCOL_VERSION` ist aber ein Alias auf die
  MODERNE Aera — gesichert war damit die Aera, in der heute praktisch niemand
  spricht, waehrend die andere frei wandern konnte. Man sieht es dem
  Konstantennamen nicht an.

  **Der Wert der Konstante aendert sich nicht.** Er war richtig, nur
  unvollstaendig beschrieben. Neu steht er gegen `LATEST_MODERN_VERSION` —
  dieselbe Zahl, aber die Aera ist benannt —, die Handshake-Obergrenze bekommt
  eine eigene Zusicherung, und ein dritter Test haelt die Alias-Eigenschaft
  fest, damit die Falle beim naechsten Lesen benannt dasteht.

  Ohne gemessenen Teil: dieser Server baut keine ASGI-App, durch die sich ein
  `initialize` schicken liesse. Die Aushandlung steht in
  `mcp/server/runner.py::_negotiate_initialize` und haengt an keinem Transport
  — an neun Schwester-Servern gemessen, hier an den SDK-Konstanten gehalten.

  **README.de.md stand drei Revisionen hinter README.md** und nannte dazu
  `mcp[cli] >= 1.3.0 (FastMCP)` — eine Anforderung von vor der Migration auf
  `mcp` 2.x, mit einem SDK-Namen, den dieser Server nicht verwendet. Die
  englische Fassung war beim letzten Mal nachgezogen worden, die deutsche
  nicht. Der Test, der die SDK-Anforderung gegen `pyproject.toml` haelt, prueft
  jetzt beide Sprachen.

- **`Mcp-Session-Id` ist weiterhin freigegeben — und das steht jetzt in einem
  Test statt in einem Satz.** Der Docstring von `tests/test_cors.py` nannte den
  Header die Spur einer Mechanik, die `2026-07-28` abgeschafft habe. Das stimmt
  nicht: `mcp` 2.x bedient beide Protokoll-Aeren, die Session gehoert zur
  Handshake-Aera, und der Server gibt den Header nicht ohne Grund auch in
  `expose_headers` frei.

  Nachgemessen statt aus Spec-Text geschlossen: `MCP_SESSION_ID_HEADER` steht
  unveraendert in `mcp/server/streamable_http.py`, und ein echter `initialize`
  durch den zusammengebauten ASGI-Stack bekommt eine Session-ID im
  Antwort-Header zurueck.

  `test_der_session_header_ist_weiterhin_freigegeben` haelt beides fest. Die
  Gegenprobe zeigt, dass es die Luecke wirklich gab: nimmt man den Header aus
  der Freigabeliste, faellt genau dieser eine Test, und die sieben bestehenden
  bleiben gruen.

### Changed

- **Drei Tests patchten eine Naht, die der Code nicht mehr benutzt.**
  `api_client` legt den Backoff-Schlaf seit laengerem als `_sleep` offen, doch
  `tests/test_api_client.py` ersetzte weiterhin `api_client.asyncio.sleep` —
  also `sleep` auf dem geteilten stdlib-Modul, prozessweit. Wirkung hatte es
  dort keine, weil diese Tests `net.safe_get` faelschen und nie in den Retry
  laufen; die Gefahr blieb trotzdem. Jetzt patchen sie `api_client._sleep`,
  wie conftest und die Retry-Tests es bereits taten.

### Behoben

- **Jede Antwort nennt jetzt den Stand des Bestands, nicht nur den des
  Caches.** Das ist bei einer Rechtssammlung die Angabe, die zählt, und sie
  fehlte.

  Gemessen am 2026-08-08: Die jüngste Fassung im gesamten Datensatz trägt
  `version_active_since = 2023-01-01`; der HuggingFace-Datensatz selbst wurde
  zuletzt am 2024-10-10 angefasst. Der Cache gilt derweil 24 Stunden, und
  `provenance="cache"` liest sich wie «aus dem Zwischenspeicher geliefert».

  Beides beantwortet die Frage «woher kam diese Antwort». Wer fragt «ist das
  aktuell?», meint «wie alt sind die Gesetze darin» — und darauf gab es keine
  Antwort. Neu tragen alle Antworten `corpus_as_of` und `corpus_note` neben
  `provenance`.

- **`zhlaw_update_cache` legte eine Wirkung nahe, die es nicht hat.** Sein
  Docstring lautete «Nur aufrufen wenn Gesetzes-Suchergebnisse veraltet
  wirken». Das Werkzeug lädt denselben eingefrorenen Datensatz erneut
  herunter; die Gesetze werden dadurch keinen Tag jünger. Ein Assistent, der
  den Docstring las, rief es auf und meldete dem Nutzer anschliessend
  dieselben Fassungen von 2023 als frisch geladen.

  Der Docstring nennt jetzt den Bestandsstand und verweist für den geltenden
  Wortlaut auf den ZH-Lex-Permalink.

- **Aufhebungen nach dem Stichtag waren unsichtbar, und nichts wies darauf
  hin.** Alle 974 Einträge tragen `is_active = True`, kein einziger führt ein
  `version_inactive_since`.

  Das ist **kein Fehler dieses Servers** — die Quelle führt ausschliesslich die
  zum Aufnahmezeitpunkt geltenden Erlasse. Der Nullbefund steht trotzdem
  aufgezeichnet in `tests/fixtures/bestand_stand.json`, damit er beim nächsten
  Durchgang nicht erneut als Fehler vermutet wird. Die Folge zählt und steht
  jetzt in `corpus_note`: Ein seither aufgehobenes Gesetz erscheint weiterhin
  als in Kraft.

### Hinzugefügt

- **`scripts/record_fixtures.py`, `tests/fixtures/` und `PROVENANCE.md`.** Der
  Recorder misst den Bestandsstand aus dem Cache des Servers und bricht ab,
  wenn er sich ändert — auch dann, wenn er *neuer* wird. Ein neuerer Bestand
  ist eine gute Nachricht und genau deshalb ein Anlass, `BESTAND_STAND`,
  README und CHANGELOG nachzuziehen, statt die Prüfung anzupassen.

- **`tests/test_bestand_stand.py`** — 8 Tests, die **in** der CI laufen.
  Gegengeprüft mit drei Rückmutationen: `corpus_as_of` aus dem Envelope
  entfernen, `BESTAND_STAND` auf ein falsches Datum setzen, die alte
  Docstring-Formulierung zurückholen. Alle drei machen die Suite rot.

- **Die Grenzen der eigenen Messung sind mit aufgezeichnet.**
  `test_live_get_law_metadata` scheiterte in der Aufzeichnungsumgebung, weil
  `zhlex.zh.ch` von dort nicht erreichbar war.

  **Daraus folgt nichts über den Server.** Das öffentliche DNS führt den Host
  (NOERROR, 194.247.8.174), gegengeprüft mit einer NXDOMAIN-Kontrolle auf einen
  erfundenen Namen. Die Grenze liegt bei der Umgebung, nicht bei der Quelle.

  Der Test ist deshalb **unangetastet** geblieben. Ein Test, den man rot sieht,
  weil das eigene Netz nicht hinauskommt, gehört nicht umgeschrieben — danach
  misst er die eigene Umgebung statt die Quelle. Dieselbe Verwechslung hat in
  diesem Portfolio schon mehrfach zu falschen Befunden geführt.

### Geändert

- **Retry-Politik gegenüber zh.ch: begrenzt, gestreut, gehorsam (`ARCH-014`).**
  Ein Portfolio-Durchlauf des Audit-Katalogs am 2026-08-07 las die Schleife in
  `fetch_zhlex_metadata` von Hand. Vier Eigenschaften fehlten.

  | Eigenschaft | Vorher | Jetzt |
  |---|---|---|
  | 5xx / 429 | **gar nicht wiederholt** — endete sofort als Fehler-Dict | wiederholt |
  | Netzfehler | nur `TimeoutException` und `ConnectError` | zusätzlich die Oberklasse `RequestError` |
  | Jitter | keiner — feste Leiter 1 s, 2 s | gestreut in `[0.5x, 1.5x]` |
  | `Retry-After` | nicht gelesen | gelesen (beide RFC-9110-Formen), schlägt die eigene Kurve |
  | Deckel | keiner | `METADATA_MAX_DELAY`, **nach** dem Jitter |
  | Zeitbudget | keines | `METADATA_TOTAL_BUDGET = 25.0` an `asyncio.timeout` |

  **Der schwerste Punkt ist der erste.** Ein 503 von zh.ch lief in den
  `httpx.HTTPStatusError`-Zweig und wurde dort zu `{"found": False, "error":
  "HTTP 503"}` — ohne einen zweiten Versuch. Der Server hatte eine
  Retry-Schleife, die den häufigsten transienten Fall nicht abdeckte: Ein
  überlastetes Gateway ist eine Aussage über den Moment, kein Ergebnis.

  **Und ein zweiter, leiserer:** Ein Verbindungsabbruch, der weder
  `TimeoutException` noch `ConnectError` heisst — etwa `httpx.ReadError` —
  fiel in den `except Exception`-Zweig und wurde ebenfalls zum Fehler-Dict.
  Gefangen wird jetzt die Oberklasse.

  **Eine deterministische Leiter ist ein Retry-Sturm:** Jeder Client, der
  denselben Ausfall trifft, kommt im selben Moment zurück, und die Last kehrt
  als Welle wieder — genau wenn sich die Quelle erholt.

  **`REQUEST_TIMEOUT` war nie ein Budget.** httpx begrenzt pro Operation, und
  sein Read-Timeout beginnt mit jedem Chunk von vorn. Drei Versuche gegen einen
  Upstream, der die vollen 30 s braucht, sind anderthalb Minuten in einem
  Tool-Aufruf, und `METADATA_MAX_ATTEMPTS` sagt das nirgends. Die 25 s hängen
  jetzt an `asyncio.timeout` und liegen unter dem 30-s-Default des MCP-SDK.

### Hinzugefügt

- **`tests/test_retry_policy.py`** — der Retry-Pfad hatte zwei Tests, beide
  über Timeouts. Die neuen decken alle sechs Eigenschaften ab, jede mit
  Gegenprobe.

- **Die Backoff-Naht liegt jetzt in `tests/conftest.py`** und gilt für die
  ganze Suite: `api_client._sleep` statt `asyncio.sleep`. Ein
  `monkeypatch.setattr(api_client.asyncio, "sleep", ...)` sähe lokal aus und
  legt das Schlafen prozessweit still — samt fremder Tests, die damit dem
  Event-Loop das Wort geben. Nebeneffekt: Die beiden bestehenden Retry-Tests
  schlafen nicht mehr echt, die Suite wird um rund 3,3 s schneller.

## [0.2.5] - 2026-08-02

### Fixed

- **`structlog` carried no upper bound, and the index already serves a major past
  the floor.** The declared range was `structlog>=24.1.0`; PyPI has been serving
  `26.1.0`. The artefact does not change — the resolver's answer to the next
  fresh install does, and that is exactly how `swiss-energy-mcp` 0.3.3 became
  uninstallable when `mcp` 2.0.0 removed the module it imported.

  Now `structlog>=24.1.0,<27`. The bound is measured rather than guessed: this package
  installs and imports against `structlog 26.1.0` today, so the cap admits what
  demonstrably works and stops only the next, unknown major.

A dependency range only reaches users through a new release, hence the
version bump. No code changed.

## [v0.2.4] — 2026-07-30

### Fixed

- **The User-Agent reports the actual package version again.** The published
  `0.2.3` sent `openlex-mcp/0.2.0` to every upstream — the version string was
  hardcoded and had been left behind by earlier bumps. The version now comes
  from the package metadata, so it can no longer drift from the package.

- **HTTP-Modus wies unter jedem echten Hostnamen mit 421 ab (SEC-005).**
  `_build_http_app()` rief `mcp.streamable_http_app()` ohne `host` auf. Unter
  mcp 2.x ist das kein neutraler Default: das SDK leitet daraus eine Allow-List
  ab und aktiviert bei loopback-artigem Wert automatisch `127.0.0.1:*`. Da der
  Default `127.0.0.1` ist, galt das auch für den `MCP_HOST=0.0.0.0`-Bind des
  Containers. Nachgemessen an der echten ASGI-App vor dem Fix:

      Host 127.0.0.1:8000        -> 200
      Host mcp.example.ch        -> 421
      Host openlex.example.com   -> 421

  `/healthz` antwortete weiter mit 200 und verdeckte es, weshalb ein
  Readiness-Probe nichts gemerkt hätte.

  Der Bind reist jetzt in die App, und eine explizite Allow-List wird aus dem
  neuen `MCP_ALLOWED_HOSTS` gebaut. Ohne diese Variable bleibt der Schutz auf
  einem Nicht-Loopback-Bind bewusst aus und der Aufrufer warnt — eine geratene
  Liste würde genau das 421-Problem reproduzieren. Konfigurierte CORS-Origins
  werden mit aufgenommen, sonst weist der Transport genau die Browser-Clients
  ab, die CORS erlaubt.

  13 neue Tests, davon der tragende „richtiger Hostname, falscher Port": nur er
  unterscheidet eine portgenaue Allow-List von einer, die alles durchlässt —
  `evil.example.com` allein würde auch ein zurückfallender Loopback-Default
  abweisen. Mutationsgetestet: nimmt man den `host`-Kwarg wieder weg,
  reproduziert der Test das 421 exakt.

  Geprüft mit dem wörtlichen CI-Kommando: 111 passed, 8 deselected;
  `ruff check src/ tests/` clean.


### Added
- **Security policy** — `SECURITY.md` (English) and `SECURITY.de.md` (German),
  linked from both READMEs and `CONTRIBUTING.md`.
- **German contribution guide** — `CONTRIBUTING.de.md`, linked from
  `CONTRIBUTING.md`.

### Fixed
- **Capped `mcp` at `<2`.** `mcp` 2.0.0, published 2026-07-28, removed
  `mcp.server.fastmcp` — the module this server imports. With the previous
  unbounded `>=1.28.1` every fresh resolve picked 2.0.0 and failed at import
  with `ModuleNotFoundError`, in CI and for anyone running `pip install` alike.
  Verified in both directions: 2.0.0 fails, `<2` resolves to 1.29.0 and imports
  cleanly. Migrating to the 2.x API (`mcp.server.mcpserver`) stays a separate,
  deliberate piece of work.

- **`zhlaw_get_law_metadata` permalink** — the legacy
  `http://www.zhlex.zh.ch/Erlass.html?Open&Ordnr=<ordnr>` permalink was replaced
  upstream and now returns 404 (it redirected to a `lawcollection-directlink`
  endpoint that 404s over HTTP). Metadata now resolves via the current
  `https://www.zhlex.zh.ch/bin/zhweb/publish/lawcollection-directlink?Open&Ordnr=<ordnr>`
  endpoint, which 302-redirects to the consolidated version on `www.zh.ch`.
- **Live tests** — repaired three nightly live-test regressions caused by upstream
  drift:
  - `zhlaw_get_article` returned empty `content` for single-line PDF extracts
    (e.g. VSG § 1): the article parser captured the whole running text into the
    title. The parser now derives the marginal-note title and the body separately
    so `content` is never empty for run-on lines. Offline regression tests added.
  - `zhlaw_get_law_metadata` no longer resolved on zh.ch — the undated
    `erlass-<ordnr>.html` landing URL was removed upstream (returns 404). Live
    metadata now uses the stable per-ordinance permalink
    `http://www.zhlex.zh.ch/Erlass.html?Open&Ordnr=<ordnr>`, which redirects to
    the current consolidated version on `www.zh.ch`.
  - `test_live_list_laws` asserted a brittle SR-prefix that does not hold for the
    first page (laws are sorted ascending by ordinance number); it now checks the
    real invariant (non-empty, ascending `sr_number`s).

### Changed
- **Egress allow-list (SEC-021 / SEC-004)** — added `www.zhlex.zh.ch` to
  `EGRESS_ALLOWLIST` and introduced `HTTP_ALLOWED_HOSTS` so that this single
  legacy permalink host may be reached over HTTP (it has no HTTPS endpoint).
  HTTPS remains mandatory for every other host; the allow-list, SSRF IP-block,
  DNS-pinning, and per-hop redirect gate are unchanged. See
  `docs/network-egress.md`.
- **Documentation consistency** — re-synced `README.de.md` with the English
  `README.md` (Development Phase, network binding, expanded cloud config, design
  decision, scaling constraints, MCP protocol version, tool output format,
  security rows, updated project tree). Updated `LICENSE` copyright year to 2026.

## [v0.2.0] — 2026-05-29

First production-ready release. Resolves all 31 findings from the initial MCP
best-practice audit plus the 4 findings from the follow-up re-audit
(2026-05-29T112502-Z): 40/44 checks pass, 0 fail, `production_ready: true`.
SCALE-002/003 remain documented accepted-risk Phase-2 gates.

### Changed
- **ARCH-002**: all 8 tool docstrings now carry structured `<use_case>`,
  `<important_notes>`, and `<example>` tags. The tags disambiguate similar tools
  (e.g. `find_education_laws` vs `search_laws`, `get_article` vs
  `search_articles`), surface caveats (FTS5 syntax, content truncation, live-HTTP
  cost, cache-vs-live), and give concrete example inputs. `docs/tool-hashes.json`
  updated to reflect the new description hashes.
- **SDK-002** (breaking — tool output contract): all 8 tools now return a typed,
  structured response envelope (`openlex_mcp/responses.py`) instead of
  pre-formatted Markdown strings. Each envelope carries `source`, `provenance`
  (`Literal["cache","live","parser","cache+parser","none"]`), `result_type`
  (`Literal`), `count`, an optional human-readable `message`, and a typed
  `results` list (`LawSummary` / `LawDetail` / `ArticleItem` / `MetadataItem` /
  `CacheStatusItem`). FastMCP now emits an output schema + `structuredContent`
  for every tool. "Not found" / "no results" are conveyed via `count=0` +
  `message` (still normal results, not `isError`).

### Added
- **OBS-003**: structured logging via `structlog` (`openlex_mcp/logging_config.py`).
  JSON to **stderr**, RFC-5424 severities (debug/info/warning/error/critical),
  and per-tool-call bound context (`tool` name + a fresh `correlation_id`).
  Each tool logs a `tool_call` event; `_fail` logs `tool_execution_failed` with
  the bound context and exception info. `structlog>=24.1.0` added as a runtime
  dependency. `MCP_PROTOCOL_VERSION` / tool-hash snapshot now also covers the
  new output schemas.
- **ARCH-011**: repository structure verified complete — `src/` layout,
  populated `tests/` (89 tests), `README.md` + `README.de.md`, `CHANGELOG.md`,
  `ROADMAP.md`, `LICENSE`, `pyproject.toml`, and `.github/workflows/`.
- **SDK-001**: a FastMCP `lifespan` (`@asynccontextmanager`) now manages a
  single, process-wide shared `httpx.AsyncClient` instead of constructing a new
  client on every `zhlaw_get_law_metadata` call; the client is closed on
  lifespan shutdown.
- **SDK-004**: CORS middleware on the Streamable-HTTP app exposes/allows the
  `Mcp-Session-Id` header for browser clients. Origins are configured explicitly
  via `MCP_CORS_ORIGINS` (comma-separated) — **no wildcard default**. The HTTP
  transport is now served via `uvicorn` over the CORS-wrapped app.

### Changed
- **OBS-001 / OBS-002**: tool execution errors are now surfaced as masked
  `isError` results (via `ToolError`) instead of being returned as plain text.
  The catch-all error handler no longer leaks the exception type/message to the
  LLM; the original error (with traceback) is logged to **stderr** only. Logging
  is now explicitly configured to stderr in `main()` (`LOG_LEVEL` env override),
  keeping stdout reserved for the JSON-RPC stream (OBS-004). Legitimate
  "not found" / "no results" responses remain normal guidance results.

### Security
- **SEC-004 / SEC-021 / SEC-005**: all outbound HTTP requests now go through a
  hardened gate (`openlex_mcp/net.py`): HTTPS-only enforcement, a code-layer
  egress allow-list (`frozenset`, `www.zh.ch`), SSRF IP-blocking of
  private/loopback/link-local/metadata ranges (incl. `169.254.169.254`), and
  DNS-pinning (resolve once, connect to the validated IP, preserve `Host` + TLS
  SNI). Redirects are followed manually and re-validated against the full chain.
  The shared HTTP client no longer auto-follows redirects. New
  `docs/network-egress.md` documents the policy and the network-layer companion.
- **SEC-016**: HTTP transport now defaults to `127.0.0.1` instead of hardcoded
  `0.0.0.0`. Host/port are configurable via `MCP_HOST`/`MCP_PORT` env vars (or
  `--host`/`--port`). Binding to `0.0.0.0` outside a detected container logs a
  NeighborJack warning. Cloud deployments must set `MCP_HOST=0.0.0.0` explicitly.

### Fixed
- `User-Agent` header no longer contains a non-ASCII character (`Zürich` →
  `Zuerich`), which made `zhlaw_get_law_metadata` raise `UnicodeEncodeError`.

### Added
- **OPS-001** (live tests): `tests/test_live.py` adds 8 `@pytest.mark.live` tests
  (one per tool) that exercise the real upstreams — a module-scoped fixture loads
  the full HuggingFace dataset once, and `test_live_get_law_metadata` makes a real
  HTTP request to zh.ch. New `.github/workflows/live.yml` runs them nightly
  (04:00 UTC) and on manual `workflow_dispatch`; regular CI continues to exclude
  them via `-m "not live"`. No credentials required (public APIs).
- **OPS-001** (unit tests): test suite under `tests/` (89 unit tests) covering the
  law parser, SQLite/FTS5 cache, zh.ch client (respx-mocked), tool handlers, input
  validation, and the SEC-016 binding logic. Removed an unused `StrEnum` import.
- **SEC-007 / SCALE-004**: multi-stage `Dockerfile` for the Render cloud
  deployment. Builder stage installs deps; slim `python:3.11-slim` runtime stage
  runs as non-root `appuser` (uid/gid 10001). `MCP_HOST=0.0.0.0` is set in the
  image (Render sets `RENDER`, suppressing the NeighborJack warning). A
  `HEALTHCHECK` polls `http://localhost:8000/health` every 30 s. A
  `.dockerignore` excludes tests, audits, editor artefacts, and SQLite data
  files (the DB is built at runtime from HuggingFace).
- **SEC-019**: Lethal Trifecta assessment added to README Safety & Limits table:
  score 1/3 (public data only, GET-only egress, no code execution). Safe by
  design; rationale now captured for future maintainers.
- **SEC-009**: Session-handling posture documented in README: `Mcp-Session-Id`
  is generated by the MCP SDK (cryptographically secure); no user-identity
  binding is performed (`auth_model=none` — correct for public read-only data).
  Pre-condition to add OAuth binding noted in ROADMAP.md transition gates.
- **SEC-013**: `docs/secret-management.md` added documenting the Public Open
  Data / no-secrets posture (Stufe 1). Enumerates all env vars (none secret) and
  the upgrade path if credentials are ever introduced.
- **OPS-003**: Development phase declared in README (Phase 1 — read-only).
  `ROADMAP.md` added with completed items, Phase 1 planned work, and explicit
  Phase 1 → Phase 2 transition gates.
- **SCALE-002 / SCALE-003**: Scaling constraints documented in README
  Architecture section: in-process session state means single-instance only;
  horizontal scaling requires a shared session store or sticky-session LB routing
  on `Mcp-Session-Id`.
- **SEC-022**: All 8 tool names now carry the `openlex__` server-identity prefix
  (`openlex__zhlaw_search_laws`, …). `docs/tool-hashes.json` introduced as a
  release-time SHA-256 snapshot of each tool's name + description + parameter
  schema; `scripts/gen_tool_hashes.py` regenerates it. Tool-definition changes
  must now be noted in the CHANGELOG.
- **SEC-018**: `strict=True` added to all 8 Pydantic input model configs —
  prevents type coercion (e.g. `"20"` → `20`, `1` → `True`) at the tool
  boundary. New edge-case tests cover over-length strings, out-of-range numeric
  bounds, and strict-mode coercion rejection.
- **ARCH-012**: `MCP_PROTOCOL_VERSION = "2025-11-25"` constant added to
  `server.py`; README "MCP Protocol Version" section documents the supported
  version, SDK pin, and update policy. `.github/dependabot.yml` enables weekly
  Dependabot PRs for pip and GitHub Actions dependencies.
- **ARCH-004 / SCALE-001**: `Settings` class (`pydantic-settings`) replaces
  scattered `os.environ.get` calls in `server.py`. All runtime config is now in
  one place: `MCP_HOST`, `MCP_PORT`, `MCP_TRANSPORT`, `MCP_CORS_ORIGINS`,
  `LOG_LEVEL`. `MCP_TRANSPORT=streamable-http` selects HTTP mode without the
  `--http` CLI flag (which still works for backward compatibility). Dockerfile
  now sets `MCP_TRANSPORT=streamable-http` via `ENV`; CMD no longer passes
  `--http`. `pydantic-settings>=2.0.0` added as a runtime dependency.
- **SCALE-006**: `compose.yml` added with explicit memory (512 m limit / 256 m
  reservation), CPU (0.5 vCPU limit), and FD (`nofile` 1024/2048) resource
  limits for local testing. Mirrors the recommended Render Starter plan. Restart
  policy `unless-stopped` and a named volume for the SQLite cache included.
- **SDK-003**: `ctx: Context` added to `zhlaw_update_cache`; `ctx.info()` on
  start and completion, `ctx.report_progress(0/1 → 1/1)` around the
  HuggingFace load, and `ctx.warning()` on error-status results. Progress is
  now surfaced to the MCP client during the ~25 s initial dataset download.
- **ARCH-008**: Tools-only design decision documented in README Architecture
  section — all endpoints are parametric, the 974-law corpus is too large for
  static Resource URIs, and URI-template Resources are noted as a Phase-2
  consideration.
- **OBS-006 / SEC-014 / SEC-015**: Acknowledged as accepted-risk and recorded
  in `ROADMAP.md` "Deferred / Accepted Risk" table. Each is gated on Phase 2
  prerequisites (multi-tenant exposure, authentication, distributed tracing
  need) and not actionable for the current single-tenant, public-data profile.

## [0.1.0] - 2026-04-12

### Added
- Initial release with 8 MCP tools for Canton Zurich legislation
- **Search tools**: `zhlaw_search_laws`, `zhlaw_list_laws`, `zhlaw_find_education_laws`
- **Retrieval tools**: `zhlaw_get_law`, `zhlaw_get_law_metadata`
- **Article tools**: `zhlaw_get_article`, `zhlaw_search_articles`
- **Cache tools**: `zhlaw_update_cache`
- Local SQLite + FTS5 cache with automatic HuggingFace data loading (974 ZH laws)
- Article parser supporting Art./§ notation and superscript paragraph digits
- Hybrid architecture: cached full-text (HuggingFace) + live metadata (zh.ch)
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud)
- Bilingual documentation (EN/DE)
