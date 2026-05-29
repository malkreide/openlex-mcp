## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Single-instance Render deployment documented in README; FastMCP keeps streamable-http session state in-process

### Expected Behavior

Sticky sessions or shared session state with an explicit TTL, validated by a failover test (or documented single-instance constraint).

### Evidence / Gaps

- No sticky-session / shared-state (Redis, Durable Objects) mechanism — horizontal scaling would break sessions
- No explicit session TTL; no failover handling/test
- Acceptable only for single-instance deploy; not documented as such

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Either document the single-instance constraint explicitly, or add a shared-state session store (Redis) / sticky-session config with an explicit TTL before horizontal scaling.

### Effort Estimate

M

### Verification After Fix

Re-run check SCALE-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
