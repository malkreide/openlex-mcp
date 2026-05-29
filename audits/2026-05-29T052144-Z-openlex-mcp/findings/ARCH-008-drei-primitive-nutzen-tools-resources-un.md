## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-008` |
| **PDF-Reference** | Anhang A2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Server uses the Tools primitive exclusively (8 tools)

### Expected Behavior

At least two primitives used, or a documented justification for tools-only.

### Evidence / Gaps

- No Resources or Prompts primitives, and no README justification for tools-only
- Deterministic read-only lookups (get_law, get_article) are good Resources-migration candidates

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Either expose deterministic read-only lookups (get_law, get_article) as MCP Resources, or document in the README why a tools-only design was chosen.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-008 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
