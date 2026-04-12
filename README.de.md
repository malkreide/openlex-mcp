[🇬🇧 English Version](README.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# ⚖️ openlex-mcp

![Version](https://img.shields.io/badge/version-0.1.0-blue)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Kein API-Schlüssel](https://img.shields.io/badge/Auth-keiner%20erforderlich-brightgreen)](https://github.com/malkreide/openlex-mcp)

> MCP-Server für die Zürcher Gesetzessammlung (ZH-Lex) — Volltextsuche, Artikelextraktion und Bildungsrecht-Tools für ~970 kantonale Gesetze

---

## Übersicht

`openlex-mcp` ermöglicht KI-Assistenten den direkten Zugang zur gesamten Rechtssammlung des Kantons Zürich. Der Server kombiniert Volltextdaten von HuggingFace mit Live-Metadaten der offiziellen zh.ch-Website und speichert alles in einer lokalen SQLite-Datenbank mit FTS5-Volltextindex für Suchzeiten unter 50ms.

| Quelle | Daten | Zugriff |
|--------|-------|---------|
| **HuggingFace** | 974 ZH-Gesetze — Volltext (PDF-Extrakte) | Lokal als SQLite + FTS5 gecacht |
| **zh.ch ZH-Lex** | Aktuelle Metadaten, PDF-Links, Gültigkeitsstatus | Live HTTP-Anfragen |

Entwickelt für das Schulamt der Stadt Zürich, aber deckt alle kantonalen Rechtsgebiete ab — von Steuerrecht bis Bauvorschriften.

**Anker-Demo-Abfrage:** *«Was sagt das Volksschulgesetz über Elternmitwirkung? Zeige Art. 55 VSG und finde alle Artikel, die ‹Elternrat› erwähnen.»*

---

## Funktionen

- ⚖️ **8 Tools** für Suche, Abruf, Artikelextraktion und Cache-Verwaltung
- 🔍 **FTS5-Volltextsuche** über ~970 kantonale Gesetze mit BM25-Ranking
- 📑 **Artikelextraktion** — einzelne Artikel (Art. / §) mit Absatzerkennung
- 🏫 **Bildungsrecht-Schnellsuche** — spezialisierte Suche in der LS 412.x Serie (Volksschulgesetz, Lehrpersonalverordnung etc.)
- 🌐 **Live-Metadaten** von zh.ch für aktuellen Gültigkeitsstatus und PDF-Links
- 💾 **Hybrid-Architektur** — gecachter Volltext (HuggingFace) + Live-Metadaten (zh.ch)
- 🔓 **Kein API-Schlüssel erforderlich** — alle Daten unter offenen Lizenzen (CC-BY-SA 4.0)
- ☁️ **Dualer Transport** — stdio (Claude Desktop) + Streamable HTTP (Cloud)

---

## Voraussetzungen

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (empfohlen) oder pip
- Internetverbindung (für initialen Datendownload und Live-Metadaten)

---

## Installation

```bash
# Repository klonen
git clone https://github.com/malkreide/openlex-mcp.git
cd openlex-mcp

# Installieren
pip install -e .
# oder mit uv:
uv pip install -e .
```

---

## Schnellstart

```bash
# stdio (für Claude Desktop)
python -m openlex_mcp.server

# Streamable HTTP (Port 8000)
python -m openlex_mcp.server --http --port 8000
```

Sofort in Claude Desktop ausprobieren:

> *«Was ist das Volksschulgesetz (VSG)?»*
> *«Finde alle Zürcher Gesetze zum Datenschutz»*
> *«Zeige Art. 1 des Volksschulgesetzes»*
> *«Welche Bildungsgesetze erwähnen ‹Schulleitung›?»*

---

## Konfiguration

### Claude Desktop

Editiere `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) bzw. `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "openlex": {
      "command": "python",
      "args": ["-m", "openlex_mcp.server"]
    }
  }
}
```

Oder mit dem installierten Entry Point:

```json
{
  "mcpServers": {
    "openlex": {
      "command": "openlex-mcp"
    }
  }
}
```

**Pfad zur Konfigurationsdatei:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### Cloud-Deployment (SSE für Browser-Zugriff)

Für den Einsatz via **claude.ai im Browser** (z.B. auf verwalteten Arbeitsplätzen ohne lokale Software-Installation):

**Render.com (empfohlen):**
1. Repository auf GitHub pushen/forken
2. Auf [render.com](https://render.com): New Web Service → GitHub-Repo verbinden
3. Start-Befehl setzen: `python -m openlex_mcp.server --http --port 8000`
4. In claude.ai unter Settings → MCP Servers eintragen: `https://your-app.onrender.com/sse`

> 💡 *«stdio für den Entwickler-Laptop, SSE für den Browser.»*

---

## Verfügbare Tools

### Suche & Abruf

| Tool | Beschreibung |
|------|-------------|
| `zhlaw_search_laws` | Volltextsuche über alle ~970 ZH-Gesetze (FTS5 + BM25-Ranking) |
| `zhlaw_get_law` | Gesetz nach LS-Nummer (z.B. `412.100`) oder Abkürzung (z.B. `VSG`) abrufen |
| `zhlaw_list_laws` | Gesetze nach Rechtsgebiet-Prefix auflisten und filtern |
| `zhlaw_find_education_laws` | Spezialisierte Suche im Bildungsrecht (LS 412.x Serie) |

### Artikelextraktion

| Tool | Beschreibung |
|------|-------------|
| `zhlaw_get_article` | Einzelnen Artikel aus einem Gesetz extrahieren (z.B. Art. 28 VSG) |
| `zhlaw_search_articles` | In allen Artikeln eines Gesetzes suchen |

### Metadaten & Cache

| Tool | Beschreibung |
|------|-------------|
| `zhlaw_get_law_metadata` | Aktuelle Metadaten von zh.ch abrufen (PDF-Links, Gültigkeit) |
| `zhlaw_update_cache` | Lokalen Cache von HuggingFace aktualisieren |

### Wichtige Rechtsgebiet-Prefixe (LS-Nummern)

| Prefix | Rechtsgebiet | Beispiel |
|--------|-------------|----------|
| `131` | Verfassung und Volksrechte | Kantonsverfassung |
| `170` | Verwaltungsrechtspflege | Datenschutzgesetz |
| `331` | Steuerrecht | Steuergesetz |
| `412` | Bildung und Schule | Volksschulgesetz (VSG) |
| `700` | Raumplanung und Bau | Planungs- und Baugesetz |
| `810` | Gesundheit | Gesundheitsgesetz |

### Beispiel-Abfragen

| Abfrage | Tool |
|---------|------|
| *«Was ist das Volksschulgesetz?»* | `zhlaw_get_law` |
| *«Finde Gesetze zum Datenschutz»* | `zhlaw_search_laws` |
| *«Zeige Art. 55 VSG»* | `zhlaw_get_article` |
| *«Welche Bildungsgesetze erwähnen Schulleitung?»* | `zhlaw_find_education_laws` |
| *«Finde alle Artikel über Elternrat im VSG»* | `zhlaw_search_articles` |
| *«Ist LS 412.100 noch in Kraft?»* | `zhlaw_get_law_metadata` |

---

## Architektur

```
┌─────────────────┐     ┌──────────────────────────────┐     ┌──────────────────────────┐
│   Claude / KI   │────▶│  OpenLex MCP                 │────▶│  HuggingFace             │
│   (MCP Host)    │◀────│  (MCP Server)                │◀────│  rcds/swiss_legislation   │
└─────────────────┘     │                              │     │  (974 ZH-Gesetze, cache) │
                        │  8 Tools                     │     ├──────────────────────────┤
                        │  SQLite + FTS5 Cache         │────▶│  zh.ch ZH-Lex            │
                        │  Stdio | HTTP                │◀────│  (Live-Metadaten + PDFs) │
                        │                              │     ├──────────────────────────┤
                        │  Keine Authentifizierung     │     │  LexFind.ch              │
                        └──────────────────────────────┘     │  (nur Links)             │
                                                             └──────────────────────────┘
```

### Datenquellen-Übersicht

| Quelle | Protokoll | Umfang | Auth | Lizenz |
|--------|-----------|--------|------|--------|
| HuggingFace `rcds/swiss_legislation` | Datasets API | 974 ZH-Gesetze (Volltext) | Keine | CC-BY-SA 4.0 |
| zh.ch ZH-Lex | HTTP/HTML | Aktuelle Metadaten, PDFs | Keine | Öffentlich |
| LexFind.ch | HTTP | Interkantonale Links | Keine | Öffentlich |

---

## Projektstruktur

```
openlex-mcp/
├── src/openlex_mcp/
│   ├── __init__.py              # Package
│   ├── __main__.py              # Einstiegspunkt für python -m
│   ├── server.py                # 8 MCP Tool-Definitionen (FastMCP)
│   ├── api_client.py            # zh.ch HTTP-Client + Metadaten-Extraktion
│   ├── data_cache.py            # SQLite + FTS5 Cache-Management
│   └── law_parser.py            # Artikelextraktion aus Gesetzestexten
├── tests/
│   └── test_server.py           # Unit + Integrationstests
├── .github/workflows/ci.yml     # GitHub Actions (Python 3.11/3.12/3.13)
├── pyproject.toml
├── claude_desktop_config.json   # Beispiel-Konfiguration für Claude Desktop
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md                    # Englische Hauptversion
└── README.de.md                 # Diese Datei (Deutsch)
```

---

## Bekannte Einschränkungen

- **HuggingFace-Datensatz:** Das Feld `html_content` ist unzuverlässig (Inhalte zwischen Gesetzen vertauscht); der Server nutzt stattdessen `pdf_content`, das korrekt ist, aber PDF-Extraktionsartefakte aufweist (Silbentrennung, Layout)
- **Artikel-Parser:** PDF-Textextraktion verschmelzt manchmal Artikelgrenzen; komplex verschachtelte Artikel werden nicht immer perfekt geparst
- **Erststart:** Erster Start benötigt ~25s zum Herunterladen und Indexieren von 974 Gesetzen von HuggingFace (~38 MB SQLite-Datenbank)
- **zh.ch-Metadaten:** Keine offizielle API; Metadaten-Extraktion basiert auf HTML-Mustern, die sich ändern können
- **Offline-Modus:** Volltextsuche funktioniert offline nach Erststart; Live-Metadaten benötigen Internet

---

## Tests

```bash
# Unit-Tests (kein API-Key erforderlich)
PYTHONPATH=src pytest tests/ -m "not live"

# Integrationstests (Live-API-Aufrufe)
pytest tests/ -m "live"
```

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)

---

## Autor

Hayal Oezkan · [malkreide](https://github.com/malkreide)

---

## Credits & Verwandte Projekte

- **Daten:** [rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation) — HuggingFace-Datensatz (CC-BY-SA 4.0)
- **ZH-Lex:** [zh.ch Gesetzessammlung](https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung.html) — Offizielle Zürcher Rechtssammlung
- **LexFind:** [lexfind.ch](https://www.lexfind.ch/) — Interkantonale Gesetzesdatenbank
- **Protokoll:** [Model Context Protocol](https://modelcontextprotocol.io/) — Anthropic / Linux Foundation
- **Verwandt:** [swiss-courts-mcp](https://github.com/malkreide/swiss-courts-mcp) — Gesetzestext + Rechtsprechung = vollständige Rechtsrecherche
- **Verwandt:** [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp) — Gesetzestext + Stadtratsbeschlüsse = voller Kontext
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)
