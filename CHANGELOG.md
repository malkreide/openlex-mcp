# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-12

### Added
- Initial release
- 8 MCP tools for Canton Zurich legislation
- `zhlaw_search_laws` — full-text search across ~970 cantonal laws (SQLite FTS5 with BM25 ranking)
- `zhlaw_get_law` — retrieve law by LS number (e.g., `412.100`) or abbreviation (e.g., `VSG`)
- `zhlaw_get_article` — extract individual articles from law texts with paragraph detection
- `zhlaw_list_laws` — list and filter laws by legal area prefix
- `zhlaw_find_education_laws` — specialized search in education law (LS 412.x series)
- `zhlaw_search_articles` — search within all articles of a specific law
- `zhlaw_get_law_metadata` — live metadata from zh.ch (PDF links, validity status)
- `zhlaw_update_cache` — refresh local cache from HuggingFace
- Local SQLite + FTS5 cache with automatic HuggingFace data loading
- Article parser supporting Art./paragraph notation and superscript digits
- Hybrid architecture: cached full-text (HuggingFace) + live metadata (zh.ch)
- Dual transport support: stdio (local) and streamable-http (cloud)
