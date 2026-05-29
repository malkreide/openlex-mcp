## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- (no positive evidence — check failed outright)

### Expected Behavior

Multi-stage Dockerfile, slim base, non-root user, healthcheck, small final image.

### Evidence / Gaps

- No Dockerfile present at all — no multi-stage build, no slim base, no non-root USER, no HEALTHCHECK for the documented cloud (Render) deployment

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a multi-stage Dockerfile (builder + slim runtime) with a non-root USER and a HEALTHCHECK for the cloud deployment.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
