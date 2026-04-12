# openlex-mcp

![Version](https://img.shields.io/badge/version-0.1.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)
![MCP](https://img.shields.io/badge/MCP-FastMCP-purple)

> MCP-Server fuer die Zuercher Gesetzessammlung (ZH-Lex) — Volltextsuche, Artikelextraktion und Bildungsrecht-Tools fuer ~970 kantonale Gesetze.

[English Version](README.md)

## Uebersicht

**openlex-mcp** gibt LLM-Agenten strukturierten Zugang zur gesamten Rechtssammlung des Kantons Zuerich. Der Server kombiniert Volltextdaten von HuggingFace mit Live-Metadaten der offiziellen zh.ch-Website und speichert alles in einer lokalen SQLite-Datenbank mit FTS5-Volltextindex fuer Suchzeiten unter 50ms.

Entwickelt fuer das Schulamt der Stadt Zuerich, aber deckt alle kantonalen Rechtsgebiete ab — von Steuerrecht bis Bauvorschriften.

## Funktionen

- **Volltextsuche** ueber ~970 kantonale Gesetze mit BM25-Ranking (SQLite FTS5)
- **Artikelextraktion** — einzelne Artikel (Art. / Paragraphen) aus jedem Gesetz extrahieren
- **Bildungsrecht-Schnellsuche** — spezialisierte Suche in der LS 412.x Serie (Volksschulgesetz, Lehrerpersonalverordnung etc.)
- **Live-Metadaten** von zh.ch fuer aktuellen Gueltigkeitsstatus und PDF-Links
- **Lokaler SQLite-Cache** mit automatischem HuggingFace-Download (funktioniert offline nach Erststart)
- **Hybrid-Architektur** — gecachter Volltext (HuggingFace) + Live-Metadaten (zh.ch)

## Voraussetzungen

- Python 3.11+
- Internetverbindung (fuer initialen Datendownload und Live-Metadaten)

## Installation

```bash
# Aus Quellcode
git clone https://github.com/malkreide/openlex-mcp.git
cd openlex-mcp
pip install -e .

# Oder direkt
pip install git+https://github.com/malkreide/openlex-mcp.git
```

## Verwendung

### Mit Claude Desktop

In die Claude Desktop Konfiguration (`claude_desktop_config.json`) einfuegen:

```json
{
  "mcpServers": {
    "openlex-mcp": {
      "command": "openlex-mcp"
    }
  }
}
```

### Mit Claude Code

In den MCP-Einstellungen hinzufuegen:

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
# stdio-Transport (Standard)
openlex-mcp

# HTTP-Transport
openlex-mcp --http --port 8000
```

## Tools

| Tool | Beschreibung | Datenquelle |
|------|-------------|-------------|
| `zhlaw_search_laws` | Volltextsuche in allen ZH-Gesetzen | SQLite FTS5 |
| `zhlaw_get_law` | Gesetz nach LS-Nummer oder Abkuerzung abrufen (z.B. `412.100` oder `VSG`) | SQLite |
| `zhlaw_get_article` | Einzelnen Artikel extrahieren (z.B. Art. 28 VSG) | SQLite + Parser |
| `zhlaw_list_laws` | Gesetze auflisten mit optionalen Filtern | SQLite |
| `zhlaw_find_education_laws` | Spezialisierte Suche im Bildungsrecht (LS 412.x) | SQLite FTS5 |
| `zhlaw_search_articles` | Innerhalb aller Artikel eines Gesetzes suchen | SQLite + Parser |
| `zhlaw_get_law_metadata` | Aktuelle Metadaten von zh.ch abrufen | zh.ch live |
| `zhlaw_update_cache` | Lokalen Cache aktualisieren | HuggingFace |

### Wichtige Rechtsgebiet-Prefixe (LS-Nummern)

| Prefix | Rechtsgebiet |
|--------|-------------|
| `131` | Verfassung und Volksrechte |
| `170` | Verwaltungsrechtspflege |
| `331` | Steuerrecht |
| `412` | Bildung und Schule |
| `700` | Raumplanung und Bau |
| `810` | Gesundheit |

## Datenquellen

| Quelle | Inhalt | Zugriff |
|--------|--------|---------|
| [rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation) (HuggingFace) | Volltext von 974 ZH-Gesetzen | Lokal als SQLite + FTS5 gecacht |
| [zh.ch ZH-Lex](https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung.html) | Aktuelle Metadaten, PDF-Links | Live HTTP-Anfragen |
| [LexFind.ch](https://www.lexfind.ch/fe/de/entities/26) | Interkantonale Gesetzesdatenbank | Nur Links |

**Lizenz**: Gesetzesdaten sind CC-BY-SA 4.0 (HuggingFace-Datensatz von rcds).

## Konfiguration

Der Server benoetigt keine API-Keys. Beim ersten Start werden automatisch ~970 Gesetze von HuggingFace heruntergeladen (~25s) und in einer lokalen SQLite-Datenbank gespeichert (`data/zhlex_cache.db`, ~38 MB). Folgende Starts nutzen die gecachten Daten.

| Einstellung | Standard | Beschreibung |
|-------------|----------|-------------|
| Cache-Ort | `data/zhlex_cache.db` | SQLite-Datenbankpfad |
| Cache-Maximalalter | 24 Stunden | Schwelle fuer Auto-Refresh |
| Request-Timeout | 30 Sekunden | HTTP-Timeout fuer zh.ch |

## Projektstruktur

```
openlex-mcp/
├── src/openlex_mcp/
│   ├── __init__.py          # Package Init
│   ├── __main__.py          # Einstiegspunkt fuer python -m
│   ├── server.py            # 8 MCP Tool-Definitionen (FastMCP)
│   ├── api_client.py        # zh.ch HTTP-Client + Metadaten-Extraktion
│   ├── data_cache.py        # SQLite + FTS5 Cache-Management
│   └── law_parser.py        # Artikelextraktion aus Gesetzestexten
├── tests/                   # Test-Suite
├── data/                    # SQLite-Cache (gitignored)
├── pyproject.toml           # Projektmetadaten + Abhaengigkeiten
├── README.md                # Englische Dokumentation
├── README.de.md             # Deutsche Dokumentation
├── CHANGELOG.md             # Versionsverlauf
└── LICENSE                  # MIT-Lizenz
```

## Synergien mit anderen MCP-Servern

| Server | Kombination |
|--------|------------|
| [swiss-courts-mcp](https://github.com/malkreide/swiss-courts-mcp) | Gesetzestext + Rechtsprechung = vollstaendige Rechtsrecherche |
| [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) | Gesetzestext + Stadtratsbeschluesse = voller Kontext |

## Aenderungsprotokoll

Siehe [CHANGELOG.md](CHANGELOG.md)

## Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)

## Autor

Hayal Oezkan · [GitHub](https://github.com/malkreide)
