## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-021` |
| **PDF-Reference** | Anhang B5 + B12 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Effective egress is constrained: upstream hosts are hardcoded constants (ZHLEX_BASE, LEXFIND_BASE in api_client.py:25-26) plus HuggingFace for dataset download

### Expected Behavior

Outbound requests checked against a frozenset allow-list at the code layer and constrained at the network layer; documented.

### Evidence / Gaps

- No code-layer egress allow-list (frozenset) and no assert_host_allowed pre-request check
- No network-layer egress control (NetworkPolicy/Security Group) and no docs/network-egress.md
- follow_redirects=True can leave the intended host without an allow-list gate

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a code-layer egress allow-list (frozenset of permitted hosts) with an assert_host_allowed() pre-request check, document it in docs/network-egress.md, and add a network-layer egress control for the cloud deployment.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-021 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.
