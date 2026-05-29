## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Anhang B4 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All tools share a consistent 'zhlaw_' namespace prefix (server.py tool names)
- CHANGELOG.md is present for change tracking

### Expected Behavior

Tools carry a server-identity namespace prefix; tool-definition hashes are snapshotted and change-logged.

### Evidence / Gaps

- Prefix is 'zhlaw_' rather than the '<server>__<tool>' server-identity format the check specifies
- No tool-definition hash snapshot is generated/stored at release time; no CHANGELOG convention for tool-definition changes / re-approval

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Adopt the '<server>__<tool>' namespace prefix and generate a tool-definition hash snapshot at release time; note tool-definition changes in the CHANGELOG.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-022 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
