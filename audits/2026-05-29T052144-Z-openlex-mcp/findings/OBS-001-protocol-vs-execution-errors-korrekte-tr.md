## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Every tool wraps its body in try/except and routes failures through api_client.handle_error (server.py:397, 439, 505, ...)
- handle_error maps httpx status/timeout/connect errors to friendly messages (api_client.py:197-219)

### Expected Behavior

Application errors surface as isError:true tool-results; protocol errors use standard JSON-RPC codes; both paths are tested.

### Evidence / Gaps

- Application errors are returned as a plain Markdown string, not via the MCP isError:true tool-result mechanism — the LLM cannot distinguish success from failure programmatically
- No tests cover either execution-error or protocol-error paths (no tests/ directory at all)

### Risk Description

Gap relative to the best-practice catalog for a high-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Return application errors via the MCP isError:true tool-result mechanism rather than a plain string, and add tests covering both an execution-error path and a protocol-error path.

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
