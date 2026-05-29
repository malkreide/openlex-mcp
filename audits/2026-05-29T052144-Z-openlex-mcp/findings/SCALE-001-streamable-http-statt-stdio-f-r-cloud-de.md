## Finding: SCALE-001 — Streamable HTTP statt stdio für Cloud-Deployments

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-001` |
| **PDF-Reference** | Sec 5.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Streamable-HTTP transport is implemented for cloud (server.py:842); stdio is the local default; no WebSocket code present

### Expected Behavior

Env-based transport selection; cloud uses streamable-http; no WebSocket code.

### Evidence / Gaps

- Transport selection is via the '--http' CLI flag, not the ENV-based selection the check expects (MCP_TRANSPORT)

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Select transport via an MCP_TRANSPORT env var (stdio|streamable-http) in addition to / instead of the --http CLI flag.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
