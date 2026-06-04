# Security Policy

[🇩🇪 Deutsche Version](SECURITY.de.md)

This server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Supported Versions

Only the latest released version receives security updates.

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅        |
| < 0.2   | ❌        |

---

## Reporting a Vulnerability

Please report security vulnerabilities **privately** — do not open a public GitHub issue.

- Use [GitHub Security Advisories](https://github.com/malkreide/openlex-mcp/security/advisories/new) (preferred), or
- Email **hayal.oezkan@gmail.com** with the subject `SECURITY: openlex-mcp`.

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce (proof of concept if possible)
- Affected version(s) and environment

You can expect an initial response within **5 business days**. Once a fix is
released, we are happy to credit you in the advisory unless you prefer to remain
anonymous.

---

## Security Posture

`openlex-mcp` is a **read-only, zero-auth** MCP server over public open data. It
is structurally low-risk by design.

| Aspect | Details |
|--------|---------|
| **Access** | Read-only (`readOnlyHint: true`) — the server cannot modify or delete any data |
| **Personal data** | None — all sources are aggregated, public legal texts |
| **Secrets** | None held — all data sources are public (see [docs/secret-management.md](docs/secret-management.md)) |
| **Authentication** | No API keys required (`auth_model=none`) |
| **Lethal Trifecta** | Score **1 / 3**: public data only (no private/sensitive data) ✓ · GET-only egress to `*.zh.ch` — no POST, no webhooks, no email ✓ · no code execution ✓ |

### Network egress hardening

Outbound requests from the server's HTTP client are restricted by a code-layer
allow-list ([`src/openlex_mcp/net.py`](src/openlex_mcp/net.py)), enforced before
every request **and every redirect hop**:

- **HTTPS by default** — `http://` is permitted only for the legacy permalink
  host `www.zhlex.zh.ch`
- **Host allow-list** — only `www.zh.ch` and `www.zhlex.zh.ch`
- **SSRF IP block** — private / loopback / link-local / carrier-grade-NAT ranges
  and the cloud metadata address `169.254.169.254` are rejected
- **DNS pinning** — connections are pinned to the validated IP to close the
  TOCTOU / DNS-rebinding window

See [docs/network-egress.md](docs/network-egress.md) for the full policy and the
recommended network-layer defense in depth.

### Network binding

The HTTP transport binds to **`127.0.0.1`** (localhost only) by default. Never
bind to `0.0.0.0` outside a container — it exposes the server to your local
network (NeighborJack risk). For containerized/cloud deployments set
`MCP_HOST=0.0.0.0` explicitly; outside a detected container the server logs a
warning.

### Sessions

`Mcp-Session-Id` values are generated and managed by the MCP SDK
(cryptographically secure UUIDs). There is no user-identity binding, which is
correct for public read-only data. If authentication is ever added, bind
sessions to the validated OAuth `sub` claim before deployment.

---

## Scope

This policy covers the `openlex-mcp` server code. Vulnerabilities in upstream
data sources (HuggingFace, zh.ch) or in third-party dependencies should be
reported to their respective maintainers; dependency updates are tracked via
weekly Dependabot PRs.
