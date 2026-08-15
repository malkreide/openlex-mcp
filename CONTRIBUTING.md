# Contributing to openlex-mcp

[🇩🇪 Deutsche Version](CONTRIBUTING.de.md)

Thank you for your interest in contributing! This server is part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide).

---

## Reporting Issues

Use [GitHub Issues](https://github.com/malkreide/openlex-mcp/issues) to report bugs or request features.

Please include:
- Python version and OS
- Full error message or description of unexpected behaviour
- Steps to reproduce

For **security vulnerabilities**, please follow the [Security Policy](SECURITY.md) instead of opening a public issue.

---

## Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `PYTHONPATH=src pytest tests/ -m "not live"`
5. Commit using [Conventional Commits](https://www.conventionalcommits.org/): `feat: add new tool`
6. Push and open a Pull Request against `main`

---

## Code Style

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- Type hints required for all public functions
- Tests required for new tools
- Follow the existing FastMCP / Pydantic v2 patterns in `server.py`

---

## Data Sources

This server uses two open data sources — all without authentication:

| Source | Documentation |
|--------|--------------|
| HuggingFace `rcds/swiss_legislation` | [huggingface.co/datasets/rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation) |
| zh.ch ZH-Lex | [zh.ch Gesetzessammlung](https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung.html) |

When adding new data sources, follow the **No-Auth-First** principle: use only open, authentication-free endpoints.

---

## The live suite: when it runs, and who sees a red result

**Cadence:** daily 04:00 UTC, plus on demand via *Actions → Live Tests (nightly + manual) → Run
workflow*. See [`.github/workflows/live.yml`](.github/workflows/live.yml).

**Who sees it:** a red run opens an issue titled `Live-Tests gegen lexfind.ch rot …` with the
`upstream` label, and comments on the existing one instead of opening a second.
A run that goes green again closes it.

**Three answers, not two.** `scripts/classify_live_run.py` reads the JUnit XML rather than
the exit code and separates `clear` (ran, green), `finding` (ran, something
fell) and `unknown` (did not run — install failed, nothing collected,
everything skipped). An `unknown` never closes an issue: closing would claim a
comparison that never happened.

**A red live run does not necessarily mean *our* bug.** It means the contract
with the source has changed, or the source is down. Both belong seen; only the
first belongs fixed. Please read the run before disabling the job — that is how
this check dies, and it is the only one in the repository that can contradict a
wrong assumption about lexfind.ch. Every other test asserts against a fixture, and
the fixture was written from the same assumption as the code.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
