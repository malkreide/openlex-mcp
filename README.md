# openlex-mcp

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![MCP](https://img.shields.io/badge/MCP-FastMCP-purple)

> MCP Server for Canton Zurich legislation (ZH-Lex) — full-text search, article extraction, and education law tools for ~970 cantonal laws.

[Deutsche Version](README.de.md)

## Overview

**openlex-mcp** provides LLM agents with structured access to the entire legal collection of Canton Zurich (Kanton Zuerich Rechtssammlung). It combines full-text data from HuggingFace with live metadata from the official zh.ch website, storing everything in a local SQLite database with FTS5 full-text indexing for sub-50ms search performance.

Built for the Schulamt (school department) of the City of Zurich, but covers all areas of cantonal law — from tax law to building regulations.

## Features

- **Full-text search** across ~970 cantonal laws with BM25 ranking (SQLite FTS5)
- **Article extraction** — parse individual articles (Art. / paragraphs) from any law
- **Education law shortcuts** — specialized search for LS 412.x series (Volksschulgesetz, Lehrpersonalverordnung, etc.)
- **Live metadata** from zh.ch for current validity status and PDF links
- **Local SQLite cache** with automatic HuggingFace data loading (works offline after first load)
- **Hybrid architecture** — cached full-text (HuggingFace) + live metadata (zh.ch)

## Prerequisites

- Python 3.11+
- Internet connection (for initial data download and live metadata)

## Installation

```bash
# From source
git clone https://github.com/malkreide/openlex-mcp.git
cd openlex-mcp
pip install -e .

# Or directly
pip install git+https://github.com/malkreide/openlex-mcp.git
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "openlex-mcp": {
      "command": "openlex-mcp"
    }
  }
}
```

### With Claude Code

Add to your MCP settings:

```json
{
  "openlex-mcp": {
    "command": "openlex-mcp",
    "type": "stdio"
  }
}
```

### Standalone

```bash
# stdio transport (default)
openlex-mcp

# HTTP transport
openlex-mcp --http --port 8000
```

## Tools

| Tool | Description | Data Source |
|------|-------------|------------|
| `zhlaw_search_laws` | Full-text search across all ZH laws | SQLite FTS5 |
| `zhlaw_get_law` | Get a law by LS number or abbreviation (e.g., `412.100` or `VSG`) | SQLite |
| `zhlaw_get_article` | Extract a specific article from a law (e.g., Art. 28 VSG) | SQLite + Parser |
| `zhlaw_list_laws` | List laws with optional filters (by legal area prefix) | SQLite |
| `zhlaw_find_education_laws` | Specialized search in education law (LS 412.x series) | SQLite FTS5 |
| `zhlaw_search_articles` | Search within all articles of a specific law | SQLite + Parser |
| `zhlaw_get_law_metadata` | Get live metadata from zh.ch (PDF links, validity) | zh.ch live |
| `zhlaw_update_cache` | Refresh the local data cache from HuggingFace | HuggingFace |

### Key Legal Area Prefixes (LS Numbers)

| Prefix | Legal Area |
|--------|-----------|
| `131` | Constitution and popular rights |
| `170` | Administrative procedure |
| `331` | Tax law |
| `412` | Education and schools |
| `700` | Spatial planning and building |
| `810` | Health |

## Data Sources

| Source | Content | Access |
|--------|---------|--------|
| [rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation) (HuggingFace) | Full text of 974 ZH laws | Cached locally as SQLite + FTS5 |
| [zh.ch ZH-Lex](https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung.html) | Current metadata, PDF links | Live HTTP requests |
| [LexFind.ch](https://www.lexfind.ch/fe/de/entities/26) | Cross-cantonal law database | Links only |

**License**: Law data is CC-BY-SA 4.0 (HuggingFace dataset by rcds).

## Configuration

The server requires no API keys. On first use, it automatically downloads ~970 laws from HuggingFace (~25s) and stores them in a local SQLite database (`data/zhlex_cache.db`, ~38 MB). Subsequent starts use the cached data.

| Setting | Default | Description |
|---------|---------|-------------|
| Cache location | `data/zhlex_cache.db` | SQLite database path |
| Cache max age | 24 hours | Auto-refresh threshold |
| Request timeout | 30 seconds | HTTP timeout for zh.ch |

## Project Structure

```
openlex-mcp/
├── src/openlex_mcp/
│   ├── __init__.py          # Package init
│   ├── __main__.py          # Entry point for python -m
│   ├── server.py            # 8 MCP tool definitions (FastMCP)
│   ├── api_client.py        # zh.ch HTTP client + metadata extraction
│   ├── data_cache.py        # SQLite + FTS5 cache management
│   └── law_parser.py        # Article extraction from law texts
├── tests/                   # Test suite
├── data/                    # SQLite cache (gitignored)
├── pyproject.toml           # Project metadata + dependencies
├── README.md                # English documentation
├── README.de.md             # German documentation
├── CHANGELOG.md             # Version history
└── LICENSE                  # MIT License
```

## Synergies with Other MCP Servers

| Server | Combination |
|--------|------------|
| [swiss-courts-mcp](https://github.com/malkreide/swiss-courts-mcp) | Law text + case law = complete legal research |
| [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) | Law text + city council decisions = full context |

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## License

MIT License — see [LICENSE](LICENSE)

## Author

Hayal Oezkan · [GitHub](https://github.com/malkreide)
