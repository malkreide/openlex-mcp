## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-016` |
| **PDF-Reference** | Sec 4 (Empirie 2025) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- src/openlex_mcp/server.py:842 — mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

### Expected Behavior

HTTP listener binds to localhost by default; 0.0.0.0 only inside container contexts via explicit env override.

### Evidence / Gaps

- 0.0.0.0 is hardcoded as the only HTTP host, with no 127.0.0.1 default and no MCP_HOST env override (NeighborJack risk on dev laptops / shared networks)
- No container-detection warning when binding to 0.0.0.0 outside a container
- No Dockerfile/README differentiation between local (127.0.0.1) and container (0.0.0.0) binding

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Default the HTTP host to 127.0.0.1 and only bind 0.0.0.0 via an explicit MCP_HOST env var; warn when binding 0.0.0.0 outside a container; document the local/container split in the README.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-016 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
