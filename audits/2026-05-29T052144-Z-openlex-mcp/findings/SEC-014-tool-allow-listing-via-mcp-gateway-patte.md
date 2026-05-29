## Finding: SEC-014 — Tool-Allow-Listing via MCP-Gateway-Pattern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-014` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All 8 tools are read-only/non-sensitive public-data tools; no gateway needed today

### Expected Behavior

Default-deny tool allow-listing per role with audited denials.

### Evidence / Gaps

- No tool allow-listing / MCP-gateway default-deny pattern and no denied-call auditing (low priority for public read-only data)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If multi-tenant/enterprise exposure arrives, add a default-deny tool allow-list at a gateway with denied-call auditing; low priority for public read-only data today.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-014 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
