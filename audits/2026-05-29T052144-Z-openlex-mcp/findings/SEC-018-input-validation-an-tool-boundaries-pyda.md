## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-018` |
| **PDF-Reference** | Sec 3 / Sec 4 (Defense-in-Depth) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All 8 tools use Pydantic input models with extra="forbid" and str_strip_whitespace (server.py:89,123,...)
- Numeric fields have ge/le bounds (limit ge=1,le=50; offset ge=0); string fields have min_length/max_length; sr_number has a whitelist pattern ^\d+[\d.]*$ (server.py:236)

### Expected Behavior

All tool args validated with strict Pydantic models; edge cases covered by tests.

### Evidence / Gaps

- Pydantic strict=True is not set on the model configs
- No tests exercise edge cases (over-length strings, out-of-range numbers, unknown fields)

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Set strict=True on the Pydantic model configs and add edge-case tests (over-length strings, out-of-range numbers, unknown fields).

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-018 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
