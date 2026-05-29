## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cloud target is a single Render web service (README) — no multi-backend LB in scope today

### Expected Behavior

Edge LB routes on Mcp-Session-Id with adequate stick-table capacity and TTL; failover tested.

### Evidence / Gaps

- No edge-LB Mcp-Session-Id routing / stick-table configuration documented or provided
- No failover behaviour defined for multi-backend scale-out

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Document/provide edge-LB routing on Mcp-Session-Id with a stick-table and TTL once multi-backend scale-out is in scope; today document the single-backend constraint.

### Effort Estimate

M

### Verification After Fix

Re-run check SCALE-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
