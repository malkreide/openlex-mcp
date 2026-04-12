# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-12

### Added
- Initial release with 8 MCP tools for Canton Zurich legislation
- **Search tools**: `zhlaw_search_laws`, `zhlaw_list_laws`, `zhlaw_find_education_laws`
- **Retrieval tools**: `zhlaw_get_law`, `zhlaw_get_law_metadata`
- **Article tools**: `zhlaw_get_article`, `zhlaw_search_articles`
- **Cache tools**: `zhlaw_update_cache`
- Local SQLite + FTS5 cache with automatic HuggingFace data loading (974 ZH laws)
- Article parser supporting Art./§ notation and superscript paragraph digits
- Hybrid architecture: cached full-text (HuggingFace) + live metadata (zh.ch)
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud)
- Bilingual documentation (EN/DE)
