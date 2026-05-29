## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-001` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cache is initialised once via a module-global singleton (_get_cache, server.py:55-61) rather than per-call

### Expected Behavior

Lifespan-managed shared clients; no per-call AsyncClient construction.

### Evidence / Gaps

- No FastMCP lifespan defined via @asynccontextmanager; no AsyncExitStack
- api_client._get_client() constructs a fresh httpx.AsyncClient on every metadata call (api_client.py:72-78) instead of reusing a lifespan-scoped client

### Risk Description

Gap relative to the best-practice catalog for a high-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Define a FastMCP lifespan via @asynccontextmanager that creates one shared httpx.AsyncClient and initialises the cache; reuse the client across tool calls instead of constructing one per request.

### Effort Estimate

M

### Verification After Fix

Re-run check SDK-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
