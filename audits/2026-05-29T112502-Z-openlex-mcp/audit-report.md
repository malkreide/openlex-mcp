# MCP-Server Audit-Report — `<server>`

**Audit-Datum:** 
**Skill-Version:** ?
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `<server>` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 40 bestanden, 4 Findings dokumentiert (0 critical, 3 high, 1 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `?` |
| Audit-Datum | ? |
| Skill-Version | ? |
| Catalog-Version | ? |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Render']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 10 | 0 | 1 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 5 | 0 | 0 | 0 | 0 |
| OPS | 2 | 0 | 1 | 0 | 0 |
| SCALE | 3 | 0 | 2 | 0 | 0 |
| SDK | 4 | 0 | 0 | 0 | 0 |
| SEC | 15 | 0 | 0 | 0 | 0 |
| **Total** | **40** | **0** | **4** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| OPS-001 | OPS | high | partial |
| SCALE-002 | SCALE | high | partial |
| SCALE-003 | SCALE | high | partial |
| ARCH-002 | ARCH | medium | partial |

**Gesamt:** 4 Findings

---

## 5. Detail-Findings

### ARCH-002

## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-002` |
| **PDF-Reference** | Sec 2.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | claude-sonnet-4-6 |

### Observed Behavior

All 8 tool docstrings are 230–386 characters, well above the 50-character minimum, and contain substantive use-case context. However, no tool uses the structured XML-style tags (`<use_case>`, `<important_notes>`, `<example>`) required by the check for at least 80% of tools. There is also no negative disambiguation between similar tools (e.g., when to use `zhlaw_search_laws` vs `zhlaw_find_education_laws`).

Example (current):
```python
async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    Durchsucht Titel, Abkürzungen und Volltexte aller ~970 kantonalen Gesetze.
    Unterstützt FTS5-Syntax: AND, OR, NOT, Phrasensuche "...".
    Ergebnisse nach Relevanz sortiert (BM25-Algorithmus).

    Beispiele: 'Tagesschule', 'Datenschutz Gemeinde', 'Elternrat OR Elternmitwirkung'.
    """
```

### Expected Behavior

The check requires structured XML-style tags in at least 80% (7/8) of tools:
- `<use_case>` — when should the tool be used?
- `<important_notes>` — caveats, limitations, side-effects
- `<example>` — concrete sample inputs

```python
async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    <use_case>Wenn nach einem Rechtsbegriff in allen ~970 Zürcher Gesetzen gesucht
    werden soll. Für Bildungsrecht-spezifische Suche: openlex__zhlaw_find_education_laws
    verwenden (schneller, präziser für 412.x-Serie).</use_case>

    <important_notes>FTS5-Syntax: AND, OR, NOT, Phrasensuche "...". Ergebnisse nach
    BM25-Relevanz sortiert. Max 50 Treffer pro Aufruf. Sucht im Cache — Live-Daten
    via openlex__zhlaw_get_law_metadata.</important_notes>

    <example>query='Elternrat OR Elternmitwirkung', sr_prefix='412', limit=10</example>
    """
```

### Evidence

- `src/openlex_mcp/server.py`: 8 tool functions, none with `<use_case>`, `<important_notes>`, or `<example>` tags
- Grep: `grep -rE "<use_case>|<important_notes>|<example>" src/` returns no results
- Tool description lengths: 234–386 chars (all above minimum, but lacking structured tags)

### Risk Description

Without structured XML tags, the LLM must infer use-case boundaries from free-text descriptions. This increases the probability of the LLM choosing the wrong tool when multiple similar tools exist (e.g., `zhlaw_search_laws` vs `zhlaw_find_education_laws` vs `zhlaw_search_articles`). The gap is unlikely to cause failures but reduces disambiguation precision in ambiguous queries.

### Remediation

Add `<use_case>`, `<important_notes>`, and `<example>` tags to all 8 tool docstrings. The effort per tool is approximately 10–15 minutes.

```diff
  async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
      """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

-     Durchsucht Titel, Abkürzungen und Volltexte aller ~970 kantonalen Gesetze.
-     Unterstützt FTS5-Syntax: AND, OR, NOT, Phrasensuche "...".
-     Ergebnisse nach Relevanz sortiert (BM25-Algorithmus).
-
-     Beispiele: 'Tagesschule', 'Datenschutz Gemeinde', 'Elternrat OR Elternmitwirkung'.
+     <use_case>Allgemeine Suche in allen ~970 Zürcher Gesetzen nach Rechtsbegriffen.
+     Für Bildungsrecht (412.x) direkt: openlex__zhlaw_find_education_laws.
+     Für Artikel eines bekannten Gesetzes: openlex__zhlaw_search_articles.</use_case>
+
+     <important_notes>FTS5-Syntax: AND, OR, NOT, Phrasensuche "...". Max 50 Treffer.
+     Sucht im lokalen Cache — Aktualität via openlex__zhlaw_get_law_metadata prüfen.
+     sr_prefix filtert nach Rechtsgebiet (412=Bildung, 331=Steuern, 700=Bau).</important_notes>
+
+     <example>query='Elternrat OR Elternmitwirkung', sr_prefix='412', limit=10</example>
      """
```

### Effort Estimate

**S** — < 1 Tag. 8 tools × 15 Minuten ≈ 2 Stunden.

### Dependencies / Blockers

None.

### Verification After Fix

```bash
grep -rE "<use_case>|<important_notes>|<example>" src/openlex_mcp/server.py | wc -l
# Expected: >= 24 (3 tags × 8 tools)
```


### OPS-001

## Finding: OPS-001 — Test-Strategie: Unit-Tests mocked + Live-Tests gemarkert

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OPS-001` |
| **PDF-Reference** | Anhang C1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | claude-sonnet-4-6 |

### Observed Behavior

The server has a strong unit test suite (89 tests across 5 files, with respx mocking for HTTP) and the CI correctly runs `pytest tests/ -m "not live"`. However, **no live tests exist at all**. There is no `tests/test_live.py` file, no `@pytest.mark.live`-decorated tests, and no nightly/manual GitHub Actions workflow for live tests.

The `live` marker is registered in `pyproject.toml`:
```toml
markers = [
    "live: live API tests (skipped in CI by default)",
]
```
But no tests use this marker.

### Expected Behavior

Per the check:
- `tests/test_live.py` with at least 1 live test per tool (8 tools → ≥ 8 live tests)
- Tests decorated with `@pytest.mark.live`
- Separate nightly/manual workflow: `.github/workflows/live.yml` with `pytest -m live`

A live test validates the actual upstream APIs (zh.ch and HuggingFace) return expected schemas — catching silent API changes that unit tests with mocked responses cannot detect.

### Evidence

```bash
ls /home/user/openlex-mcp/tests/
# conftest.py  test_api_client.py  test_data_cache.py  test_law_parser.py  test_net.py  test_server.py
# No test_live.py

grep -rn "mark.live" /home/user/openlex-mcp/tests/
# (no output)

ls /home/user/openlex-mcp/.github/workflows/
# ci.yml  publish.yml
# No live.yml or nightly.yml
```

### Risk Description

Without live tests:
1. **API schema drift goes undetected**: zh.ch may change its HTML structure (the server does regex-based HTML scraping) without any automated signal
2. **HuggingFace dataset format changes** could silently break data loading without live validation
3. **Production regressions** from upstream API changes are only discovered when users report issues, not during development

The risk is medium-high for zh.ch scraping (which is acknowledged as fragile in the README: "No official API; metadata extraction relies on HTML patterns that may change").

### Remediation

**Step 1:** Create `tests/test_live.py` with live tests for each tool:

```python
"""Live-Tests für echte API-Calls (manuell / nightly, nicht in CI).

Ausführen: PYTHONPATH=src pytest -m live
"""
from __future__ import annotations

import pytest
from openlex_mcp.data_cache import LawCache


@pytest.fixture(scope="module")
def cache():
    c = LawCache()
    c.ensure_loaded()
    return c


@pytest.mark.live
async def test_live_search_laws_returns_results(cache):
    results = cache.search_fulltext("Volksschulgesetz", active_only=True, limit=5)
    assert len(results) >= 1
    assert any("Volksschul" in r["title"] for r in results)


@pytest.mark.live
async def test_live_get_metadata_from_zh_ch():
    """Tests actual HTTP request to zh.ch — catches HTML structure changes."""
    import openlex_mcp.api_client as ac
    ac.get_client()
    meta = await ac.fetch_zhlex_metadata("412.100")
    assert meta.get("found") is True
    assert "page_title" in meta


@pytest.mark.live
async def test_live_cache_loads_from_huggingface():
    c = LawCache()
    result = c.load_from_huggingface(force=False)
    assert result.get("status") in ("ok", "cache_fresh", "already_loaded")
```

**Step 2:** Create `.github/workflows/live.yml`:

```yaml
name: Live Tests (nightly + manual)

on:
  schedule:
    - cron: "0 4 * * *"  # nightly 04:00 UTC
  workflow_dispatch:

jobs:
  live-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: PYTHONPATH=src pytest -m live -v
        timeout-minutes: 10
```

### Effort Estimate

**S** — < 1 Tag. ~2 hours to write 8 live tests + workflow file.

### Dependencies / Blockers

None. Live tests for the current server need no credentials (all public APIs).

### Verification After Fix

```bash
# Run live tests
PYTHONPATH=src pytest -m live -v
# Expected: all tests pass against real APIs

# Verify CI still excludes live tests
# Check ci.yml still runs: pytest tests/ -m "not live"
```


### SCALE-002

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


### SCALE-003

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


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **OPS-001** (high, partial)
2. **SCALE-002** (high, partial)
3. **SCALE-003** (high, partial)
4. **ARCH-002** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|


_Generated by tools/build_report.py — do not edit by hand._
