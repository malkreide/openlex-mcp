## Finding: SEC-009 — Session-ID Cryptographic Binding (user_id:session_id)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-009` |
| **PDF-Reference** | Sec 4.6 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- No custom session-ID generation in src/ — Mcp-Session-Id handling is delegated to the MCP Python SDK / FastMCP streamable-http session manager (which uses cryptographically secure IDs)

### Expected Behavior

Session IDs are cryptographically generated and bound to a validated user identity; mismatches return 401/403.

### Evidence / Gaps

- No user-binding of sessions is possible because auth_model=none (no validated OAuth sub-claim to bind to) — acceptable for public read-only data but undocumented
- Session generation/binding is not asserted or tested by the server; relies entirely on SDK defaults
- Catalog applicability gap: this critical check is gated only on transport, not on the presence of per-user state — residual risk here is low for a no-auth public read-only server

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Document that session handling is delegated to the MCP SDK and that user-binding is N/A while auth_model=none; revisit this check (bind Mcp-Session-Id to the validated OAuth sub-claim) before any auth is added.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-009 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
