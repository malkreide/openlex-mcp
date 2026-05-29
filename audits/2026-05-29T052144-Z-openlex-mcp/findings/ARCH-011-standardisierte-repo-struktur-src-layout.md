## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Anhang A8 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Top-level files present: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- Correct src-layout (src/openlex_mcp/...); .github/workflows present with ci.yml + publish.yml

### Expected Behavior

Standard repo layout incl. a populated tests/ directory.

### Evidence / Gaps

- tests/ directory is missing entirely (required by the standard repo structure)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a tests/ directory (closes OPS-001 too) so the repo matches the standard structure.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-011 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
