# Network Egress Policy

This server makes outbound HTTP requests to exactly one host at runtime
(`www.zh.ch`, for live legislation metadata). Dataset downloads from HuggingFace
go through the `datasets` library, not the server's HTTP client.

## Code-layer egress allow-list (SEC-021)

All outbound requests from the server's HTTP client go through
[`openlex_mcp/net.py`](../src/openlex_mcp/net.py), which enforces, before every
request **and every redirect hop**:

1. **HTTPS only** — non-`https://` schemes are rejected (SEC-004).
2. **Host allow-list** — the host must be in `EGRESS_ALLOWLIST`
   (a `frozenset`, not runtime-mutable). Today: `www.zh.ch`.
3. **SSRF IP block** — the host is resolved once and every resulting IP is
   checked against private / loopback / link-local / carrier-grade-NAT ranges
   and the cloud metadata address `169.254.169.254` (SEC-004).
4. **DNS pinning** — the connection is pinned to the validated IP while the
   `Host` header and TLS SNI keep the original hostname, so there is no second
   DNS lookup at connect time (no TOCTOU / DNS-rebinding window) and the
   certificate is still validated against the hostname (SEC-005).

The pre-request gate is `net.assert_url_allowed(url)`; the hardened fetch helper
is `net.safe_get(client, url)`.

### Extending the allow-list

Add the host to `EGRESS_ALLOWLIST` in `src/openlex_mcp/net.py` in a reviewed
commit (it is intentionally not configurable via environment variables) and note
the change in `CHANGELOG.md`.

## Network-layer egress control (defense in depth)

The code-layer allow-list should be backed by a network-layer control in
production. Examples:

**Kubernetes NetworkPolicy** — allow egress only to `443`, deny the metadata and
private ranges:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: openlex-mcp-egress
spec:
  podSelector:
    matchLabels: { app: openlex-mcp }
  policyTypes: [Egress]
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except: [10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.0.0/16, 127.0.0.0/8]
      ports:
        - { protocol: TCP, port: 443 }
```

On managed PaaS (e.g. Render) without NetworkPolicy support, the code-layer
allow-list plus the SSRF IP block is the enforced control; if available, enable
the platform's egress firewall and (on AWS) IMDSv2 with hop-limit 1.
