## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-015` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- No tool-poisoning surface today (static, read-only, fixed upstreams)

### Expected Behavior

Pre-flight tool-poisoning detection with default-deny on high-risk tools and tests.

### Evidence / Gaps

- No pre-flight tool-poisoning detection layer (system-prompt/override/invisible-char/homoglyph patterns) and no tests for it (low priority for this profile)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If exposed via a multi-tenant gateway, add a pre-flight tool-poisoning detection layer (system-prompt/override/invisible-char/homoglyph patterns) with tests; low priority for this profile.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-015 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
