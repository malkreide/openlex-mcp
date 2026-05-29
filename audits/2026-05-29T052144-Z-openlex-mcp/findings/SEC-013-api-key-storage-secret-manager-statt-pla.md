## Finding: SEC-013 — API-Key-Storage: Secret Manager statt Plain-Text Env-Vars

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-013` |
| **PDF-Reference** | Sec 4 (Empirie 2025) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Public Open Data profile — Stufe 1 (plain env vars) is acceptable per the check; the server holds no secrets at all

### Expected Behavior

Secret-management posture documented; for Public Open Data, plain env vars are acceptable and recorded.

### Evidence / Gaps

- No docs/secret-management.md documenting the (empty) secret posture as the check requires for Public Open Data

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add docs/secret-management.md documenting the Public-Open-Data / no-secrets posture (Stufe 1 acceptable) so the decision is explicit.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-013 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
