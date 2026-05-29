# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- **SEC-016**: HTTP transport now defaults to `127.0.0.1` instead of hardcoded
  `0.0.0.0`. Host/port are configurable via `MCP_HOST`/`MCP_PORT` env vars (or
  `--host`/`--port`). Binding to `0.0.0.0` outside a detected container logs a
  NeighborJack warning. Cloud deployments must set `MCP_HOST=0.0.0.0` explicitly.

### Fixed
- `User-Agent` header no longer contains a non-ASCII character (`Zürich` →
  `Zuerich`), which made `zhlaw_get_law_metadata` raise `UnicodeEncodeError`.

### Added
- **OPS-001**: test suite under `tests/` (44 unit tests) covering the law
  parser, SQLite/FTS5 cache, zh.ch client (respx-mocked), tool handlers, input
  validation, and the SEC-016 binding logic. Removed an unused `StrEnum` import.

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
