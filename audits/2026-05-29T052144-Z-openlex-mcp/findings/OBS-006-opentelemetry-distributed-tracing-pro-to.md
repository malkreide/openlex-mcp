## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- N/A in practice for a single small read-only service

### Expected Behavior

OpenTelemetry tracing per tool-call with OTLP export and no sensitive span attributes.

### Evidence / Gaps

- No OpenTelemetry SDK / TracerProvider / OTLP exporter despite is_cloud_deployed (low priority for this workload)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If/when richer observability is needed, add the OpenTelemetry SDK with an OTLP exporter and per-tool-call spans; low priority for this workload.

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-006 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
