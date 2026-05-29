## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-004` |
| **PDF-Reference** | Sec 4.4 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Outbound host is hardcoded to https://www.zh.ch (api_client.py:25,52) — not a user-supplied URL
- sr_number is constrained by regex pattern ^\d+[\d.]*$ before URL construction (server.py:236)
- Only HTTP GET to a fixed domain; no arbitrary-URL fetch tool exists

### Expected Behavior

Every outbound request validates scheme and resolved IP against a blocklist before connecting; redirects cannot reach internal addresses.

### Evidence / Gaps

- httpx client uses follow_redirects=True (api_client.py:77) with no validation of the redirect target — a redirect could be steered to an internal/metadata IP
- No HTTPS-scheme enforcement on the resolved/redirected URL and no private-IP / 169.254.169.254 blocklist
- No egress proxy / IP-range check after DNS resolution

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add an outbound-request guard: enforce https scheme, resolve the host once, reject private/link-local/metadata IP ranges (incl. 169.254.169.254), and validate the redirect target (or disable follow_redirects for this fixed-host client).

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
