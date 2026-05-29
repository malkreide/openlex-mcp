## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Uses stdlib logging.getLogger with info/warning levels (data_cache.py:23,244,336)

### Expected Behavior

Structured JSON logging with >=4 severity levels and bound per-call context.

### Evidence / Gaps

- No structured logger (structlog/loguru) in dependencies; output is not JSON/logfmt
- No per-tool-call bound context (tool name, session_id, correlation_id)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Adopt a structured logger (structlog) with JSON/logfmt output and bind per-tool-call context (tool name, session/correlation id).

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
