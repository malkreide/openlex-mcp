## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Anhang A9 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- CHANGELOG.md present

### Expected Behavior

protocolVersion pinned; README documents the supported version and update policy; automated dependency PRs enabled.

### Evidence / Gaps

- protocolVersion is not explicitly pinned in server code (relies on SDK default)
- No 'MCP Protocol Version' README section and no documented update policy
- No Dependabot/Renovate config for SDK update PRs

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Pin the MCP protocolVersion explicitly, add a 'MCP Protocol Version' README section with an update policy, and enable Dependabot/Renovate for SDK updates.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-012 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
