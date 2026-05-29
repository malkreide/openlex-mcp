# Secret Management

## Current posture: Public Open Data (Stufe 1 — no secrets)

`openlex-mcp` holds **no secrets**. All data sources are public and require no credentials:

| Source | Auth required | Secrets held |
|--------|--------------|-------------|
| HuggingFace `rcds/swiss_legislation` | None (public dataset) | None |
| zh.ch ZH-Lex | None (public website) | None |
| LexFind.ch | None (public website) | None |

## Environment variables

The server reads the following environment variables at startup. None are secret:

| Variable | Purpose | Default | Secret? |
|----------|---------|---------|---------|
| `MCP_HOST` | HTTP bind host | `127.0.0.1` | No |
| `MCP_PORT` | HTTP bind port | `8000` | No |
| `MCP_CORS_ORIGINS` | Allowed CORS origins (comma-separated) | *(empty)* | No |
| `LOG_LEVEL` | Logging verbosity | `WARNING` | No |

## Classification

Per the MCP audit catalog: **Stufe 1** — public open-data server, no secrets. Plain environment variables are acceptable at this level and no secret manager is required.

## If secrets are added in future

If the server is extended to require credentials (API keys, OAuth client secrets, database passwords):

1. Store secrets in a secret manager (e.g., Render Environment Groups, AWS Secrets Manager, HashiCorp Vault).
2. Do **not** commit secrets to the repository or bake them into the Docker image (`ENV SECRET=...` in a Dockerfile is not acceptable for real secrets).
3. Inject at runtime via environment variables — never via CLI flags (flags appear in `ps` output and process listings).
4. Rotate secrets on any suspected exposure.
5. Classify the server posture as **Stufe 2** or higher and update this document.
6. Update `ROADMAP.md` Phase 1 → Phase 2 transition gates before deploying write/auth capabilities.
