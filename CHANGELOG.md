# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Security policy** — `SECURITY.md` (English) and `SECURITY.de.md` (German),
  linked from both READMEs and `CONTRIBUTING.md`.
- **German contribution guide** — `CONTRIBUTING.de.md`, linked from
  `CONTRIBUTING.md`.

### Fixed
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
