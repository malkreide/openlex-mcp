## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | accepted-risk |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | claude-sonnet-4-6 |

### Observed Behavior

No edge load balancer configuration exists (no `haproxy.cfg`, `nginx.conf`, Kubernetes Ingress, or deploy/ directory). The server correctly exposes `Mcp-Session-Id` in CORS headers for browser clients (SDK-004 is satisfied), and the README documents the Mcp-Session-Id header routing as a requirement before horizontal scaling:

> "Before scaling beyond one instance: either add a shared session store or configure your edge load balancer to route on the Mcp-Session-Id header with a stick-table and an appropriate TTL."

The server currently operates as a single-replica deployment, making LB routing a future concern only.

### Expected Behavior

For multi-replica deployments, an edge load balancer must route `Mcp-Session-Id` headers to the correct backend instance. HAProxy example:

```
backend mcp_backend
    mode http
    balance roundrobin
    stick-table type string len 64 size 200k expire 24h
    stick on hdr(Mcp-Session-Id)
    server mcp1 10.0.1.1:8000 check
    server mcp2 10.0.1.2:8000 check
```

Or NGINX:
```nginx
upstream mcp_backend {
    hash $http_mcp_session_id consistent;
    server mcp1.internal:8000;
    server mcp2.internal:8000;
}
```

### Evidence

```bash
find /home/user/openlex-mcp -name "haproxy.cfg" -o -name "nginx.conf" -o -name "ingress*.yaml"
# (no output — no LB config files)

ls /home/user/openlex-mcp/deploy/ 2>/dev/null || echo "No deploy/ directory"
# No deploy/ directory
```

### Risk Description

**Current risk level: LOW** for single-replica Phase 1 deployment.

If the server is scaled to multiple replicas without LB routing:
- Sessions intermittently fail when the same client hits different backend instances
- Conversation state is lost mid-session
- No data integrity risk (read-only server)

This risk is mitigated by the documented single-replica constraint.

### Accepted Risk Rationale

This finding is **accepted risk** for Phase 1:
- Single-replica deployment makes LB routing unnecessary today
- The requirement is explicitly documented in README with guidance for when it becomes needed
- SCALE-002 (shared session store) and SCALE-003 (LB routing) are paired concerns that should both be addressed when horizontal scaling is introduced
- Listed as a Phase 1 → Phase 2 prerequisite in ROADMAP.md

### Remediation (when scaling is needed)

**For Render/Railway (PaaS):** Enable sticky sessions via platform UI if available, or switch to a single-instance deployment with autoscaling limits.

**For Kubernetes:**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: openlex-mcp
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/affinity-mode: "persistent"
    nginx.ingress.kubernetes.io/session-cookie-name: "mcp-route"
    nginx.ingress.kubernetes.io/upstream-hash-by: "$http_mcp_session_id"
spec:
  rules:
  - host: openlex-mcp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: openlex-mcp
            port:
              number: 8000
```

**For HAProxy:**
```
frontend mcp_frontend
    bind *:80
    default_backend mcp_backend

backend mcp_backend
    mode http
    balance roundrobin
    stick-table type string len 128 size 50k expire 1h
    stick on hdr(Mcp-Session-Id)
    server mcp1 10.0.0.1:8000 check
    server mcp2 10.0.0.2:8000 check
```

### Effort Estimate

**M** — 1–2 Tage. LB configuration + integration testing with multi-replica setup.

### Dependencies / Blockers

- SCALE-002 (shared session store) should be addressed alongside this finding — sticky sessions and shared store are complementary controls
- Requires infrastructure provisioning for multi-replica deployment

### Verification After Fix

```bash
# Run multi-replica test:
# 1. Deploy with 3 replicas
# 2. Initialize MCP session → capture Mcp-Session-Id
# 3. Send 10 requests with same Mcp-Session-Id
# 4. Verify all requests hit same backend (check server logs for replica ID)
```
