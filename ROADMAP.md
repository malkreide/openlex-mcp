# Roadmap

## Phase 1 — Read-Only (current)

**Status:** active  
**Goal:** safe, zero-auth, read-only access to the Canton Zurich legislation corpus.

### Completed

- 8 MCP tools: search, retrieval, article extraction, cache management
- SQLite + FTS5 full-text cache (974 ZH laws)
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud)
- Hardened outbound HTTP: HTTPS-only, egress allow-list, SSRF IP-block, DNS-pinning
- CORS support for browser clients (`Mcp-Session-Id` exposure)
- Lifespan-scoped shared `httpx.AsyncClient`
- Non-root multi-stage Docker container with HEALTHCHECK
- 75-test CI suite (Python 3.11 / 3.12 / 3.13)

### Planned (Phase 1)

- Structured logging — structlog with JSON/logfmt output, per-call context binding (OBS-003)
- Pydantic v2 strict mode + structured response envelopes (SEC-018 / SDK-002)
- Progress reporting — `ctx.report_progress()` during `zhlaw_update_cache` HuggingFace load (SDK-003)
- Tool namespace prefix `openlex__<tool>` + release hash snapshot (SEC-022)
- MCP `protocolVersion` pinning + Dependabot for SDK updates (ARCH-012)
- Container CPU/memory resource limits (SCALE-006)

## Phase 1 → Phase 2 Transition Gates

Before adding write tools or external-send capabilities, **all** of the following must be in place:

1. **Authentication** — add OAuth2 / API key; bind `Mcp-Session-Id` to the validated `sub` claim (SEC-009).
2. **Per-user rate limiting** — prevent abuse at the tool-call level.
3. **Lethal Trifecta audit** — verify no new tool combines private data + write + external send (SEC-019).
4. **Shared session store** — Redis or equivalent for multi-replica Streamable-HTTP sessions (SCALE-002/003).
5. **Tool allow-list gateway** — default-deny list with auditing for denied calls (SEC-014).
6. **Update secret management posture** — move any new credentials to a secret manager (SEC-013).

## Phase 2 — Write / External-Send (future)

Not yet scoped. All Phase 1 transition gates must pass before entering this phase.

## Phase 3 — Multi-Agent (future)

Not yet scoped. Requires Phase 2 completion + shared session store for horizontal scaling.
