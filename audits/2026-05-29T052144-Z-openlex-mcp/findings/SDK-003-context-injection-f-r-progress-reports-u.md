## Finding: SDK-003 — Context Injection für Progress Reports und Logging

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-003` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cache refresh logs duration via stdlib logger (data_cache.py:244)

### Expected Behavior

Long-running tools report progress and log via Context, not silently.

### Evidence / Gaps

- zhlaw_update_cache (HuggingFace dataset load — typically >2s) takes no ctx: Context and emits no ctx.report_progress()
- No tool uses ctx.info()/ctx.warning(); errors are surfaced only as return strings

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add ctx: Context to long-running tools (esp. zhlaw_update_cache) and call ctx.report_progress()/ctx.info() during the HuggingFace load; route non-fatal issues through ctx.warning().

### Effort Estimate

S

### Verification After Fix

Re-run check SDK-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
