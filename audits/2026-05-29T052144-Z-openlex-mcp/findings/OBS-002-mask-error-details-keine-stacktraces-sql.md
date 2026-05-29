## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-002` |
| **PDF-Reference** | Sec 6.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Known error classes are masked to user-friendly text (api_client.py:201-217) — no tracebacks for HTTP/timeout/connect errors

### Expected Behavior

No raw exception text reaches the LLM; full detail stays in server logs.

### Evidence / Gaps

- The catch-all branch returns f"{type(e).__name__}: {e}" (api_client.py:219), leaking raw exception text (potentially SQLite/parse internals) to the LLM
- FastMCP is not initialised with mask_error_details=True (server.py:68-79)

### Risk Description

Gap relative to the best-practice catalog for a high-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Initialise FastMCP with mask_error_details=True and replace the catch-all 'type(e).__name__: {e}' return with a generic user-facing message while logging the original to stderr.

### Effort Estimate

S

### Verification After Fix

Re-run check OBS-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
