## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-005` |
| **PDF-Reference** | Sec 4.4 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Only a single fixed upstream host (www.zh.ch) is contacted, limiting DNS-rebinding exposure

### Expected Behavior

One DNS resolution per request, used for the TCP connection; TLS validated against the original hostname.

### Evidence / Gaps

- No DNS pinning: httpx performs its own resolution per request and follow_redirects=True allows a second resolution/target (TOCTOU window)
- No test verifying a single DNS resolution per request

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Pin DNS: resolve the upstream host once and connect to the resolved IP while preserving the Host header/SNI; add a test asserting a single resolution per request. (Lower priority given the single fixed host.)

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-005 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
