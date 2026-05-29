## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-002` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Pydantic >=2.0 in dependencies; all tools have explicit '-> str' return annotations and use Field(default=...) for defaults

### Expected Behavior

Tools return structured, typed payloads with a consistent envelope rather than opaque strings.

### Evidence / Gaps

- Tool returns are formatted Markdown strings, not a structured response envelope (source/provenance/results/count) or BaseModel/TypedDict
- No Literal types for enumerable values

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Return a structured response envelope (source/provenance/results/count) via a Pydantic model or TypedDict instead of pre-formatted Markdown strings; use Literal types for enumerable fields.

### Effort Estimate

M

### Verification After Fix

Re-run check SDK-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
