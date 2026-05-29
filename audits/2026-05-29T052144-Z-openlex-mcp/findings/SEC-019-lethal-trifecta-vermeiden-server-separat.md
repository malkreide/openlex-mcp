## Finding: SEC-019 — Lethal Trifecta vermeiden: Server-Separation Read vs Write/Send

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Anhang B1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Trifecta score is 1/3 — only public open data (no private data), only GET to fixed zh.ch (no send/POST/mail; grep for requests.post/smtplib/webhook clean), so the server is structurally safe
- All search/read tools carry readOnlyHint:true; the single write tool (zhlaw_update_cache) only refreshes the local SQLite cache

### Expected Behavior

A documented Trifecta assessment shows the server holds at most two of the three capabilities; here only one.

### Evidence / Gaps

- No documented Lethal-Trifecta assessment in README/docs (pass criterion) — design is safe but the rationale is not captured for future maintainers

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a 'Lethal Trifecta' assessment table to the README documenting score 1/3 (public data only, GET-only, no external send) so the safe design is captured for future maintainers.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-019 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
