## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-006` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- MAX_RESULTS_LIMIT=50 and content-preview caps bound per-request work (server.py:40-41, 330)

### Expected Behavior

Explicit container resource limits with requests<limits and a tested OOM/restart behaviour.

### Evidence / Gaps

- No container memory/CPU/FD limits defined (no Dockerfile/compose/k8s manifest)
- OOM/restart behaviour not defined

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Define container memory/CPU limits and an FD limit (or document the Render plan limits) and a restart policy.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-006 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
