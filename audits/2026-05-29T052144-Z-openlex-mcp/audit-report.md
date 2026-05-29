# MCP-Server Audit-Report — `openlex-mcp`

**Audit-Datum:** 2026-05-29
**Skill-Version:** 0.5.0
**Catalog-Version:** 68-checks

---

## 1. Executive Summary

Server `openlex-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 13 bestanden, 31 Findings dokumentiert (4 critical, 16 high, 11 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: OPS-001, SEC-016.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `openlex-mcp` |
| Audit-Datum | 2026-05-29 |
| Skill-Version | 0.5.0 |
| Catalog-Version | 68-checks |
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
| ARCH | 7 | 0 | 4 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 1 | 0 | 4 | 0 | 0 |
| OPS | 1 | 1 | 1 | 0 | 0 |
| SCALE | 0 | 1 | 4 | 0 | 0 |
| SDK | 0 | 0 | 4 | 0 | 0 |
| SEC | 3 | 1 | 11 | 0 | 0 |
| **Total** | **13** | **3** | **28** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-004 | SEC | critical | partial |
| SEC-009 | SEC | critical | partial |
| SEC-016 | SEC | critical | fail |
| SEC-019 | SEC | critical | partial |
| ARCH-004 | ARCH | high | partial |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | partial |
| OPS-001 | OPS | high | fail |
| OPS-003 | OPS | high | partial |
| SCALE-001 | SCALE | high | partial |
| SCALE-002 | SCALE | high | partial |
| SCALE-003 | SCALE | high | partial |
| SDK-001 | SDK | high | partial |
| SDK-004 | SDK | high | partial |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | partial |
| SEC-013 | SEC | high | partial |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-011 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | partial |
| OBS-003 | OBS | medium | partial |
| OBS-006 | OBS | medium | partial |
| SCALE-004 | SCALE | medium | fail |
| SCALE-006 | SCALE | medium | partial |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | partial |
| SEC-014 | SEC | medium | partial |
| SEC-015 | SEC | medium | partial |

**Gesamt:** 31 Findings

---

## 5. Detail-Findings

### ARCH-004

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


### ARCH-008

## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-008` |
| **PDF-Reference** | Anhang A2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Server uses the Tools primitive exclusively (8 tools)

### Expected Behavior

At least two primitives used, or a documented justification for tools-only.

### Evidence / Gaps

- No Resources or Prompts primitives, and no README justification for tools-only
- Deterministic read-only lookups (get_law, get_article) are good Resources-migration candidates

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Either expose deterministic read-only lookups (get_law, get_article) as MCP Resources, or document in the README why a tools-only design was chosen.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-008 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### ARCH-011

## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Anhang A8 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Top-level files present: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- Correct src-layout (src/openlex_mcp/...); .github/workflows present with ci.yml + publish.yml

### Expected Behavior

Standard repo layout incl. a populated tests/ directory.

### Evidence / Gaps

- tests/ directory is missing entirely (required by the standard repo structure)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a tests/ directory (closes OPS-001 too) so the repo matches the standard structure.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-011 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-012` |
| **PDF-Reference** | Anhang A9 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- CHANGELOG.md present

### Expected Behavior

protocolVersion pinned; README documents the supported version and update policy; automated dependency PRs enabled.

### Evidence / Gaps

- protocolVersion is not explicitly pinned in server code (relies on SDK default)
- No 'MCP Protocol Version' README section and no documented update policy
- No Dependabot/Renovate config for SDK update PRs

### Risk Description

Gap relative to the best-practice catalog for a medium-severity ARCH control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Pin the MCP protocolVersion explicitly, add a 'MCP Protocol Version' README section with an update policy, and enable Dependabot/Renovate for SDK updates.

### Effort Estimate

S

### Verification After Fix

Re-run check ARCH-012 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-001` |
| **PDF-Reference** | Sec 6.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Every tool wraps its body in try/except and routes failures through api_client.handle_error (server.py:397, 439, 505, ...)
- handle_error maps httpx status/timeout/connect errors to friendly messages (api_client.py:197-219)

### Expected Behavior

Application errors surface as isError:true tool-results; protocol errors use standard JSON-RPC codes; both paths are tested.

### Evidence / Gaps

- Application errors are returned as a plain Markdown string, not via the MCP isError:true tool-result mechanism — the LLM cannot distinguish success from failure programmatically
- No tests cover either execution-error or protocol-error paths (no tests/ directory at all)

### Risk Description

Gap relative to the best-practice catalog for a high-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Return application errors via the MCP isError:true tool-result mechanism rather than a plain string, and add tests covering both an execution-error path and a protocol-error path.

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### OBS-002

## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-002` |
| **PDF-Reference** | Sec 6.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Known error classes are masked to user-friendly text (api_client.py:201-217) — no tracebacks for HTTP/timeout/connect errors

### Expected Behavior

No raw exception text reaches the LLM; full detail stays in server logs.

### Evidence / Gaps

- The catch-all branch returns f"{type(e).__name__}: {e}" (api_client.py:219), leaking raw exception text (potentially SQLite/parse internals) to the LLM
- FastMCP is not initialised with mask_error_details=True (server.py:68-79)

### Risk Description

Gap relative to the best-practice catalog for a high-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Initialise FastMCP with mask_error_details=True and replace the catch-all 'type(e).__name__: {e}' return with a generic user-facing message while logging the original to stderr.

### Effort Estimate

S

### Verification After Fix

Re-run check OBS-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-003` |
| **PDF-Reference** | Sec 6.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Uses stdlib logging.getLogger with info/warning levels (data_cache.py:23,244,336)

### Expected Behavior

Structured JSON logging with >=4 severity levels and bound per-call context.

### Evidence / Gaps

- No structured logger (structlog/loguru) in dependencies; output is not JSON/logfmt
- No per-tool-call bound context (tool name, session_id, correlation_id)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Adopt a structured logger (structlog) with JSON/logfmt output and bind per-tool-call context (tool name, session/correlation id).

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- N/A in practice for a single small read-only service

### Expected Behavior

OpenTelemetry tracing per tool-call with OTLP export and no sensitive span attributes.

### Evidence / Gaps

- No OpenTelemetry SDK / TracerProvider / OTLP exporter despite is_cloud_deployed (low priority for this workload)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity OBS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If/when richer observability is needed, add the OpenTelemetry SDK with an OTLP exporter and per-tool-call spans; low priority for this workload.

### Effort Estimate

M

### Verification After Fix

Re-run check OBS-006 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


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


### OPS-003

## Finding: OPS-003 — Phasenarchitektur: Read-only First, dann Write, dann Multi-Agent

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `OPS-003` |
| **PDF-Reference** | Anhang C4 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Server is de-facto Phase 1 (read-only): all query tools are read-only, matching a Phase-1 posture

### Expected Behavior

README declares the phase; a roadmap documents phase tasks and transition gates consistent with tool annotations.

### Evidence / Gaps

- No explicit phase declaration in the README
- No roadmap file with phase-specific tasks
- Phase transitions / preconditions are not documented

### Risk Description

Gap relative to the best-practice catalog for a high-severity OPS control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Declare the current phase (Phase 1: read-only) in the README and add a ROADMAP with phase-specific tasks and transition preconditions.

### Effort Estimate

S

### Verification After Fix

Re-run check OPS-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SCALE-001

## Finding: SCALE-001 — Streamable HTTP statt stdio für Cloud-Deployments

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-001` |
| **PDF-Reference** | Sec 5.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Streamable-HTTP transport is implemented for cloud (server.py:842); stdio is the local default; no WebSocket code present

### Expected Behavior

Env-based transport selection; cloud uses streamable-http; no WebSocket code.

### Evidence / Gaps

- Transport selection is via the '--http' CLI flag, not the ENV-based selection the check expects (MCP_TRANSPORT)

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Select transport via an MCP_TRANSPORT env var (stdio|streamable-http) in addition to / instead of the --http CLI flag.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Single-instance Render deployment documented in README; FastMCP keeps streamable-http session state in-process

### Expected Behavior

Sticky sessions or shared session state with an explicit TTL, validated by a failover test (or documented single-instance constraint).

### Evidence / Gaps

- No sticky-session / shared-state (Redis, Durable Objects) mechanism — horizontal scaling would break sessions
- No explicit session TTL; no failover handling/test
- Acceptable only for single-instance deploy; not documented as such

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Either document the single-instance constraint explicitly, or add a shared-state session store (Redis) / sticky-session config with an explicit TTL before horizontal scaling.

### Effort Estimate

M

### Verification After Fix

Re-run check SCALE-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SCALE-003

## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cloud target is a single Render web service (README) — no multi-backend LB in scope today

### Expected Behavior

Edge LB routes on Mcp-Session-Id with adequate stick-table capacity and TTL; failover tested.

### Evidence / Gaps

- No edge-LB Mcp-Session-Id routing / stick-table configuration documented or provided
- No failover behaviour defined for multi-backend scale-out

### Risk Description

Gap relative to the best-practice catalog for a high-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Document/provide edge-LB routing on Mcp-Session-Id with a stick-table and TTL once multi-backend scale-out is in scope; today document the single-backend constraint.

### Effort Estimate

M

### Verification After Fix

Re-run check SCALE-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SCALE-004

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- (no positive evidence — check failed outright)

### Expected Behavior

Multi-stage Dockerfile, slim base, non-root user, healthcheck, small final image.

### Evidence / Gaps

- No Dockerfile present at all — no multi-stage build, no slim base, no non-root USER, no HEALTHCHECK for the documented cloud (Render) deployment

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a multi-stage Dockerfile (builder + slim runtime) with a non-root USER and a HEALTHCHECK for the cloud deployment.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SCALE-006

## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SCALE-006` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- MAX_RESULTS_LIMIT=50 and content-preview caps bound per-request work (server.py:40-41, 330)

### Expected Behavior

Explicit container resource limits with requests<limits and a tested OOM/restart behaviour.

### Evidence / Gaps

- No container memory/CPU/FD limits defined (no Dockerfile/compose/k8s manifest)
- OOM/restart behaviour not defined

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SCALE control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Define container memory/CPU limits and an FD limit (or document the Render plan limits) and a restart policy.

### Effort Estimate

S

### Verification After Fix

Re-run check SCALE-006 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-001` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cache is initialised once via a module-global singleton (_get_cache, server.py:55-61) rather than per-call

### Expected Behavior

Lifespan-managed shared clients; no per-call AsyncClient construction.

### Evidence / Gaps

- No FastMCP lifespan defined via @asynccontextmanager; no AsyncExitStack
- api_client._get_client() constructs a fresh httpx.AsyncClient on every metadata call (api_client.py:72-78) instead of reusing a lifespan-scoped client

### Risk Description

Gap relative to the best-practice catalog for a high-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Define a FastMCP lifespan via @asynccontextmanager that creates one shared httpx.AsyncClient and initialises the cache; reuse the client across tool calls instead of constructing one per request.

### Effort Estimate

M

### Verification After Fix

Re-run check SDK-001 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SDK-002

## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-002` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Pydantic >=2.0 in dependencies; all tools have explicit '-> str' return annotations and use Field(default=...) for defaults

### Expected Behavior

Tools return structured, typed payloads with a consistent envelope rather than opaque strings.

### Evidence / Gaps

- Tool returns are formatted Markdown strings, not a structured response envelope (source/provenance/results/count) or BaseModel/TypedDict
- No Literal types for enumerable values

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Return a structured response envelope (source/provenance/results/count) via a Pydantic model or TypedDict instead of pre-formatted Markdown strings; use Literal types for enumerable fields.

### Effort Estimate

M

### Verification After Fix

Re-run check SDK-002 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SDK-003

## Finding: SDK-003 — Context Injection für Progress Reports und Logging

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-003` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Cache refresh logs duration via stdlib logger (data_cache.py:244)

### Expected Behavior

Long-running tools report progress and log via Context, not silently.

### Evidence / Gaps

- zhlaw_update_cache (HuggingFace dataset load — typically >2s) takes no ctx: Context and emits no ctx.report_progress()
- No tool uses ctx.info()/ctx.warning(); errors are surfaced only as return strings

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add ctx: Context to long-running tools (esp. zhlaw_update_cache) and call ctx.report_progress()/ctx.info() during the HuggingFace load; route non-fatal issues through ctx.warning().

### Effort Estimate

S

### Verification After Fix

Re-run check SDK-003 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SDK-004` |
| **PDF-Reference** | Sec 3.1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- README documents browser/claude.ai access over Streamable-HTTP/SSE (README.md:124-132)

### Expected Behavior

CORS exposes/allows Mcp-Session-Id; allow_origins is an explicit non-wildcard list in production.

### Evidence / Gaps

- No CORS middleware configured in code (no CORSMiddleware/allow_origins/expose_headers)
- Mcp-Session-Id is not added to expose_headers/allow_headers — browser clients may fail to read the session header; relies on FastMCP defaults
- allow_origins is not pinned to an explicit non-wildcard list for production

### Risk Description

Gap relative to the best-practice catalog for a high-severity SDK control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Configure CORS middleware for the HTTP transport: expose and allow Mcp-Session-Id, and pin allow_origins to an explicit list for production.

### Effort Estimate

S

### Verification After Fix

Re-run check SDK-004 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-004

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


### SEC-005

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


### SEC-007

## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-007` |
| **PDF-Reference** | Sec 4.5 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Local default is stdio with no network surface; PyPI publish uses OIDC Trusted Publisher (publish.yml)

### Expected Behavior

Container runs as non-root with minimal privileges and a read-only root filesystem.

### Evidence / Gaps

- No Dockerfile at all — no non-root USER, no dropped capabilities, no read-only rootfs, no seccomp profile for the documented Render cloud deployment

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a hardened Dockerfile for the Render deployment: non-root USER (uid>=10000), dropped capabilities, read-only rootfs where possible.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-007 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-009

## Finding: SEC-009 — Session-ID Cryptographic Binding (user_id:session_id)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-009` |
| **PDF-Reference** | Sec 4.6 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- No custom session-ID generation in src/ — Mcp-Session-Id handling is delegated to the MCP Python SDK / FastMCP streamable-http session manager (which uses cryptographically secure IDs)

### Expected Behavior

Session IDs are cryptographically generated and bound to a validated user identity; mismatches return 401/403.

### Evidence / Gaps

- No user-binding of sessions is possible because auth_model=none (no validated OAuth sub-claim to bind to) — acceptable for public read-only data but undocumented
- Session generation/binding is not asserted or tested by the server; relies entirely on SDK defaults
- Catalog applicability gap: this critical check is gated only on transport, not on the presence of per-user state — residual risk here is low for a no-auth public read-only server

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Document that session handling is delegated to the MCP SDK and that user-binding is N/A while auth_model=none; revisit this check (bind Mcp-Session-Id to the validated OAuth sub-claim) before any auth is added.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-009 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-013

## Finding: SEC-013 — API-Key-Storage: Secret Manager statt Plain-Text Env-Vars

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-013` |
| **PDF-Reference** | Sec 4 (Empirie 2025) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Public Open Data profile — Stufe 1 (plain env vars) is acceptable per the check; the server holds no secrets at all

### Expected Behavior

Secret-management posture documented; for Public Open Data, plain env vars are acceptable and recorded.

### Evidence / Gaps

- No docs/secret-management.md documenting the (empty) secret posture as the check requires for Public Open Data

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add docs/secret-management.md documenting the Public-Open-Data / no-secrets posture (Stufe 1 acceptable) so the decision is explicit.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-013 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-014

## Finding: SEC-014 — Tool-Allow-Listing via MCP-Gateway-Pattern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-014` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All 8 tools are read-only/non-sensitive public-data tools; no gateway needed today

### Expected Behavior

Default-deny tool allow-listing per role with audited denials.

### Evidence / Gaps

- No tool allow-listing / MCP-gateway default-deny pattern and no denied-call auditing (low priority for public read-only data)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If multi-tenant/enterprise exposure arrives, add a default-deny tool allow-list at a gateway with denied-call auditing; low priority for public read-only data today.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-014 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-015

## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-015` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- No tool-poisoning surface today (static, read-only, fixed upstreams)

### Expected Behavior

Pre-flight tool-poisoning detection with default-deny on high-risk tools and tests.

### Evidence / Gaps

- No pre-flight tool-poisoning detection layer (system-prompt/override/invisible-char/homoglyph patterns) and no tests for it (low priority for this profile)

### Risk Description

Gap relative to the best-practice catalog for a medium-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

If exposed via a multi-tenant gateway, add a pre-flight tool-poisoning detection layer (system-prompt/override/invisible-char/homoglyph patterns) with tests; low priority for this profile.

### Effort Estimate

M

### Verification After Fix

Re-run check SEC-015 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-016

## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-016` |
| **PDF-Reference** | Sec 4 (Empirie 2025) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- src/openlex_mcp/server.py:842 — mcp.run(transport="streamable-http", host="0.0.0.0", port=port)

### Expected Behavior

HTTP listener binds to localhost by default; 0.0.0.0 only inside container contexts via explicit env override.

### Evidence / Gaps

- 0.0.0.0 is hardcoded as the only HTTP host, with no 127.0.0.1 default and no MCP_HOST env override (NeighborJack risk on dev laptops / shared networks)
- No container-detection warning when binding to 0.0.0.0 outside a container
- No Dockerfile/README differentiation between local (127.0.0.1) and container (0.0.0.0) binding

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Default the HTTP host to 127.0.0.1 and only bind 0.0.0.0 via an explicit MCP_HOST env var; warn when binding 0.0.0.0 outside a container; document the local/container split in the README.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-016 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-018` |
| **PDF-Reference** | Sec 3 / Sec 4 (Defense-in-Depth) |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All 8 tools use Pydantic input models with extra="forbid" and str_strip_whitespace (server.py:89,123,...)
- Numeric fields have ge/le bounds (limit ge=1,le=50; offset ge=0); string fields have min_length/max_length; sr_number has a whitelist pattern ^\d+[\d.]*$ (server.py:236)

### Expected Behavior

All tool args validated with strict Pydantic models; edge cases covered by tests.

### Evidence / Gaps

- Pydantic strict=True is not set on the model configs
- No tests exercise edge cases (over-length strings, out-of-range numbers, unknown fields)

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Set strict=True on the Pydantic model configs and add edge-case tests (over-length strings, out-of-range numbers, unknown fields).

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-018 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-019

## Finding: SEC-019 — Lethal Trifecta vermeiden: Server-Separation Read vs Write/Send

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-019` |
| **PDF-Reference** | Anhang B1 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- Trifecta score is 1/3 — only public open data (no private data), only GET to fixed zh.ch (no send/POST/mail; grep for requests.post/smtplib/webhook clean), so the server is structurally safe
- All search/read tools carry readOnlyHint:true; the single write tool (zhlaw_update_cache) only refreshes the local SQLite cache

### Expected Behavior

A documented Trifecta assessment shows the server holds at most two of the three capabilities; here only one.

### Evidence / Gaps

- No documented Lethal-Trifecta assessment in README/docs (pass criterion) — design is safe but the rationale is not captured for future maintainers

### Risk Description

Gap relative to the best-practice catalog for a critical-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Add a 'Lethal Trifecta' assessment table to the README documenting score 1/3 (public data only, GET-only, no external send) so the safe design is captured for future maintainers.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-019 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


### SEC-021

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


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Anhang B4 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | mcp-audit skill (Claude) |

### Observed Behavior

- All tools share a consistent 'zhlaw_' namespace prefix (server.py tool names)
- CHANGELOG.md is present for change tracking

### Expected Behavior

Tools carry a server-identity namespace prefix; tool-definition hashes are snapshotted and change-logged.

### Evidence / Gaps

- Prefix is 'zhlaw_' rather than the '<server>__<tool>' server-identity format the check specifies
- No tool-definition hash snapshot is generated/stored at release time; no CHANGELOG convention for tool-definition changes / re-approval

### Risk Description

Gap relative to the best-practice catalog for a high-severity SEC control on a dual-transport, no-auth, cloud-deployable public-data MCP server.

### Remediation

Adopt the '<server>__<tool>' namespace prefix and generate a tool-definition hash snapshot at release time; note tool-definition changes in the CHANGELOG.

### Effort Estimate

S

### Verification After Fix

Re-run check SEC-022 via the mcp-audit skill (`eval_applicability` + targeted grep/code-review) and confirm status `pass`.


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-004** (critical, partial)
2. **SEC-009** (critical, partial)
3. **SEC-016** (critical, fail)
4. **SEC-019** (critical, partial)
5. **ARCH-004** (high, partial)
6. **OBS-001** (high, partial)
7. **OBS-002** (high, partial)
8. **OPS-001** (high, fail)
9. **OPS-003** (high, partial)
10. **SCALE-001** (high, partial)
11. **SCALE-002** (high, partial)
12. **SCALE-003** (high, partial)
13. **SDK-001** (high, partial)
14. **SDK-004** (high, partial)
15. **SEC-005** (high, partial)
16. **SEC-007** (high, partial)
17. **SEC-013** (high, partial)
18. **SEC-018** (high, partial)
19. **SEC-021** (high, partial)
20. **SEC-022** (high, partial)
21. **ARCH-008** (medium, partial)
22. **ARCH-011** (medium, partial)
23. **ARCH-012** (medium, partial)
24. **OBS-003** (medium, partial)
25. **OBS-006** (medium, partial)
26. **SCALE-004** (medium, fail)
27. **SCALE-006** (medium, partial)
28. **SDK-002** (medium, partial)
29. **SDK-003** (medium, partial)
30. **SEC-014** (medium, partial)
31. **SEC-015** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `0.5.0` |
| catalog_version | `68-checks` |
| applies_when_dsl_version | `1.0` |
| policy | `fail-or-partial` |
| audit_date | `2026-05-29` |


_Generated by tools/build_report.py — do not edit by hand._
