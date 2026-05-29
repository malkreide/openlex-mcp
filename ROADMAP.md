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
- Non-root multi-stage Docker container with HEALTHCHECK + `compose.yml` resource limits
- `pydantic-settings` `Settings` class + `MCP_TRANSPORT` env var
- `openlex__` tool namespace prefix + `docs/tool-hashes.json` release snapshot
- `MCP_PROTOCOL_VERSION` pinned + Dependabot weekly PRs
- Pydantic `strict=True` input validation + 89-test CI suite (Python 3.11 / 3.12 / 3.13)
- `ctx.report_progress()` / `ctx.info()` / `ctx.warning()` in `zhlaw_update_cache` (SDK-003)
- Structured logging — `structlog` JSON output to stderr, per-call bound context (OBS-003)
- Structured response envelopes — typed Pydantic models for all 8 tools (SDK-002)

### Planned (Phase 1)

- _(no open Phase-1 items — all audit findings cleared or accepted-risk)_

## Phase 1 → Phase 2 Transition Gates

Before adding write tools or external-send capabilities, **all** of the following must be in place:

1. **Authentication** — add OAuth2 / API key; bind `Mcp-Session-Id` to the validated `sub` claim (SEC-009).
2. **Per-user rate limiting** — prevent abuse at the tool-call level.
3. **Lethal Trifecta audit** — verify no new tool combines private data + write + external send (SEC-019).
4. **Shared session store** — Redis or equivalent for multi-replica Streamable-HTTP sessions (SCALE-002/003).
5. **Tool allow-list gateway** — default-deny list with auditing for denied calls (SEC-014).
6. **Update secret management posture** — move any new credentials to a secret manager (SEC-013).

## Deferred / Accepted Risk

The following controls are acknowledged but intentionally deferred. Each will be
revisited at the Phase 1 → 2 transition (or earlier if the deployment profile changes).

| Control | Rationale for deferral |
|---------|----------------------|
| **OBS-006** — OpenTelemetry tracing | Single-instance, single-tenant, read-only service. Distributed tracing adds no actionable signal until the service is multi-replica or multi-tenant. Scheduled for Phase 2. |
| **SEC-014** — Tool allow-list gateway | All 8 tools are public read-only data. Default-deny allow-listing is only needed before multi-tenant exposure. Pre-condition: authentication (Phase 2 gate). |
| **SEC-015** — Pre-flight tool-poisoning detection | No tool-poisoning surface today (static schema, read-only, fixed upstreams). Relevant only when the server is exposed through a multi-tenant gateway with untrusted prompt inputs. Phase 2 gate. |

## Phase 2 — Write / External-Send (future)

Not yet scoped. All Phase 1 transition gates must pass before entering this phase.

## Phase 3 — Multi-Agent (future)

Not yet scoped. Requires Phase 2 completion + shared session store for horizontal scaling.
