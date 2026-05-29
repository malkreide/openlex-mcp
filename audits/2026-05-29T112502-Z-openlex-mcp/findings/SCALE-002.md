## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | accepted-risk |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | claude-sonnet-4-6 |

### Observed Behavior

The server uses FastMCP's in-process session state (no shared session store). Horizontal scaling (multiple replicas) is explicitly documented as unsupported today. The README states:

> "Single-instance only — horizontal scaling (multiple replicas) breaks active sessions because there is no shared session store (Redis, Durable Objects, etc.)."
> "No sticky-session LB needed today — a single-replica Render deployment naturally routes all requests to one process."

No Redis, Durable Objects, or external session manager is configured. The `compose.yml` deploys a single replica with no scaling config.

### Expected Behavior

For multi-replica Streamable HTTP deployments, one of:
1. **Sticky session LB**: Edge load balancer routes on `Mcp-Session-Id` header (see SCALE-003)
2. **Shared session store**: Redis or equivalent backing store for session state

The check applies when `transport == "HTTP/SSE"` and multi-replica scaling is needed.

### Evidence

```bash
# No Redis or session store dependency
grep -rE "redis|memcached|session_manager" src/ compose.yml
# (no output)

# compose.yml has no scaling directive
grep "replicas\|scale" compose.yml
# (no output)

# README explicitly documents single-instance constraint
grep "Single-instance" README.md
# "Single-instance only — horizontal scaling (multiple replicas) breaks..."
```

### Risk Description

**Current risk level: LOW** for the Phase 1 deployment profile (single-replica Render/Railway or local stdio).

If the server were scaled to multiple replicas without adding sticky sessions or a shared session store:
- Active MCP sessions would break mid-conversation when requests hit different replicas
- Users would experience silent tool-call failures or session resets
- No data loss risk (server is read-only)

The risk only materializes if horizontal scaling is attempted without first implementing SCALE-002/SCALE-003 controls.

### Accepted Risk Rationale

This finding is **accepted risk** for Phase 1:
- Single-replica deployment is explicitly documented in README
- Scaling guidance is provided: "add a shared session store OR configure your edge LB to route on the Mcp-Session-Id header with a stick-table"
- Read-only server means no data integrity risk from session loss
- Listed as a Phase 1 → Phase 2 gate item in ROADMAP.md

### Remediation (when scaling is needed)

**Option A: Shared Session Store (Redis)**

```python
# In lifespan:
import redis.asyncio as aioredis

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    redis = aioredis.from_url(os.environ["REDIS_URL"])
    # FastMCP session integration (when SDK supports it)
    ...
    yield AppContext(redis=redis)
    await redis.aclose()
```

**Option B: Sticky Sessions via LB** (see SCALE-003 finding)

Update `compose.yml` for multi-replica:
```yaml
services:
  openlex-mcp:
    deploy:
      replicas: 3
      resources: ...
```
Plus an HAProxy/NGINX reverse proxy with `Mcp-Session-Id` affinity.

### Effort Estimate

**M** — 1–3 Tage. Redis integration or LB configuration + integration tests.

### Dependencies / Blockers

- SCALE-003 (LB routing) is the infrastructure counterpart
- Should be addressed as a Phase 1 → 2 transition gate item per ROADMAP.md

### Verification After Fix

```bash
# Test multi-replica session persistence:
docker compose up --scale openlex-mcp=3 -d
# Run MCP session test: init → tool call 1 → tool call 2 → verify continuity
```
