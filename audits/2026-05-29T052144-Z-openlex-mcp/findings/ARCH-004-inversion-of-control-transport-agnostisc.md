## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Server-Logik

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-004` |
| **PDF-Reference** | Sec 2.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Server logic is transport-agnostic: identical tool handlers serve both stdio and streamable-http (server.py:835-844)
- Tools take Pydantic input models and do not reach into the raw request object

### Expected Behavior

Configuration via a Settings object; transport chosen by env var; shared setup across transports.

### Evidence / Gaps

- Configuration uses module-level globals (MAX_RESULTS_*, EDUCATION_SR_PREFIX) instead of a Pydantic-Settings object
- Transport is selected via sys.argv ('--http') rather than an environment variable
- No shared lifespan/setup hook (cache is lazily initialised via a module-global singleton)

### Risk Description

Gap relative to the best-practice catalog for a high-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Introduce a pydantic-settings Settings object for configuration and select transport via an MCP_TRANSPORT env var instead of sys.argv; keep tool logic transport-agnostic.

### Effort Estimate

M

### Verification After Fix

Re-run check ARCH-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
