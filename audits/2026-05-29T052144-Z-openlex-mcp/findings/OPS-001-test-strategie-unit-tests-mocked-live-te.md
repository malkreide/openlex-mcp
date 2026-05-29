## Finding: OPS-001 — Test-Strategie: Unit-Tests mocked + Live-Tests gemarkert

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OPS-001` |
| **PDF-Reference** | Anhang C1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- (no positive evidence — check failed outright)

### Expected Behavior

>=5 mocked unit tests per tool plus live tests behind the 'live' marker; CI green on the non-live subset.

### Evidence / Gaps

- No tests/ directory exists at all, yet pyproject.toml sets testpaths=['tests'] and ci.yml runs 'pytest tests/ -m "not live"' — CI would currently error/collect nothing
- No unit tests (respx HTTP mocking is a declared dev-dependency but unused), no live tests, no @pytest.mark.live tests despite the 'live' marker being registered

### Risk Description

Gap relative to the best-practice catalog for a high-severity OPS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Create a tests/ directory with respx-mocked unit tests per tool and at least one @pytest.mark.live test per tool; CI already runs 'pytest tests/ -m "not live"'.

### Effort Estimate

M

### Verification After Fix

Re-run check OPS-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
