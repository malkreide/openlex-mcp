## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-007` |
| **PDF-Reference** | Sec 4.5 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Local default is stdio with no network surface; PyPI publish uses OIDC Trusted Publisher (publish.yml)

### Expected Behavior

Container runs as non-root with minimal privileges and a read-only root filesystem.

### Evidence / Gaps

- No Dockerfile at all — no non-root USER, no dropped capabilities, no read-only rootfs, no seccomp profile for the documented Render cloud deployment

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a hardened Dockerfile for the Render deployment: non-root USER (uid>=10000), dropped capabilities, read-only rootfs where possible.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-007 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
