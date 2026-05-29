## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-004` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- README documents browser/claude.ai access over Streamable-HTTP/SSE (README.md:124-132)

### Expected Behavior

CORS exposes/allows Mcp-Session-Id; allow_origins is an explicit non-wildcard list in production.

### Evidence / Gaps

- No CORS middleware configured in code (no CORSMiddleware/allow_origins/expose_headers)
- Mcp-Session-Id is not added to expose_headers/allow_headers — browser clients may fail to read the session header; relies on FastMCP defaults
- allow_origins is not pinned to an explicit non-wildcard list for production

### Risk Description

Gap relative to the best-practice catalog for a high-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Configure CORS middleware for the HTTP transport: expose and allow Mcp-Session-Id, and pin allow_origins to an explicit list for production.

### Effort Estimate

S

### Verification After Fix

Re-run check SDK-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
