[🇬🇧 English Version](README.md)

> 🇨🇭 **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# ⚖️ openlex-mcp

![Version](https://img.shields.io/badge/version-0.2.0-blue)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Kein API-Schlüssel](https://img.shields.io/badge/Auth-keiner%20erforderlich-brightgreen)](https://github.com/malkreide/openlex-mcp)

> MCP-Server für die Zürcher Gesetzessammlung (ZH-Lex) — Volltextsuche, Artikelextraktion und Bildungsrecht-Tools für ~970 kantonale Gesetze

<p align="center">
  <img src="assets/demo.png" alt="Demo: Claude durchsucht Zürcher Bildungsrecht via MCP Tool Call" width="720">
</p>

---

## Übersicht

`openlex-mcp` ermöglicht KI-Assistenten den direkten Zugang zur gesamten Rechtssammlung des Kantons Zürich (Zürcher Gesetzessammlung). Der Server kombiniert Volltextdaten von HuggingFace mit Live-Metadaten der offiziellen zh.ch-Website und speichert alles in einer lokalen SQLite-Datenbank mit FTS5-Volltextindex für Suchzeiten unter 50ms.

| Quelle | Daten | Zugriff |
|--------|-------|---------|
| **HuggingFace** | 974 ZH-Gesetze — Volltext (PDF-Extrakte) | Lokal als SQLite + FTS5 gecacht |
| **zh.ch ZH-Lex** | Aktuelle Metadaten, PDF-Links, Gültigkeitsstatus | Live HTTP-Anfragen |

Entwickelt für das Schulamt der Stadt Zürich, deckt aber alle kantonalen Rechtsgebiete ab — von Steuerrecht bis Bauvorschriften.

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

## Entwicklungsphase

**Aktuelle Phase: Phase 1 — nur lesend.** Alle Tools sind nur lesend (`readOnlyHint: true`); keine Schreibzugriffe auf externe Systeme. Siehe [ROADMAP.md](ROADMAP.md) für den Phasenplan und die Übergangskriterien, bevor Schreib- oder Multi-Agent-Funktionen hinzugefügt werden.

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

# Streamable HTTP — bindet standardmässig an 127.0.0.1:8000 (nur localhost)
python -m openlex_mcp.server --http --port 8000
```

### Netzwerk-Binding

Standardmässig bindet der HTTP-Transport an **`127.0.0.1`** (nur localhost). Host
und Port sind über die Umgebungsvariablen `MCP_HOST` / `MCP_PORT` konfigurierbar
(oder über die CLI-Flags `--host` / `--port`, die Vorrang haben).

Binde **niemals** ausserhalb eines Containers an `0.0.0.0` — das macht den Server
im lokalen Netzwerk erreichbar (NeighborJack-Risiko). Für Container-/Cloud-Deployments
setze `MCP_HOST=0.0.0.0` explizit; geschieht das ausserhalb eines erkannten
Containers, protokolliert der Server eine Warnung.

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
4. Umgebungsvariable `MCP_HOST=0.0.0.0` setzen, damit der Container erreichbar ist
   (der Code-Default ist `127.0.0.1`; Render setzt die Variable `RENDER`, daher
   wird keine NeighborJack-Warnung protokolliert)
5. `MCP_CORS_ORIGINS=https://claude.ai` setzen, damit der Browser den Header
   `Mcp-Session-Id` lesen kann (kommaseparierte Liste; **kein Wildcard** — Default
   ist leer, also kein Cross-Origin-Zugriff)
6. In claude.ai unter Settings → MCP Servers eintragen: `https://your-app.onrender.com/sse`

> 💡 *«stdio für den Entwickler-Laptop, SSE für den Browser.»*

---

## Verfügbare Tools

### Suche & Abruf

| Tool | Beschreibung |
|------|-------------|
| `openlex__zhlaw_search_laws` | Volltextsuche über alle ~970 ZH-Gesetze (FTS5 + BM25-Ranking) |
| `openlex__zhlaw_get_law` | Gesetz nach LS-Nummer (z.B. `412.100`) oder Abkürzung (z.B. `VSG`) abrufen |
| `openlex__zhlaw_list_laws` | Gesetze nach Rechtsgebiet-Prefix auflisten und filtern |
| `openlex__zhlaw_find_education_laws` | Spezialisierte Suche im Bildungsrecht (LS 412.x Serie) |

### Artikelextraktion

| Tool | Beschreibung |
|------|-------------|
| `openlex__zhlaw_get_article` | Einzelnen Artikel aus einem Gesetz extrahieren (z.B. Art. 28 VSG) |
| `openlex__zhlaw_search_articles` | In allen Artikeln eines Gesetzes suchen |

### Metadaten & Cache

| Tool | Beschreibung |
|------|-------------|
| `openlex__zhlaw_get_law_metadata` | Aktuelle Metadaten von zh.ch abrufen (PDF-Links, Gültigkeit) |
| `openlex__zhlaw_update_cache` | Lokalen Cache von HuggingFace aktualisieren |

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
| *«Was ist das Volksschulgesetz?»* | `openlex__zhlaw_get_law` |
| *«Finde Gesetze zum Datenschutz»* | `openlex__zhlaw_search_laws` |
| *«Zeige Art. 55 VSG»* | `openlex__zhlaw_get_article` |
| *«Welche Bildungsgesetze erwähnen Schulleitung?»* | `openlex__zhlaw_find_education_laws` |
| *«Finde alle Artikel über Elternrat im VSG»* | `openlex__zhlaw_search_articles` |
| *«Ist LS 412.100 noch in Kraft?»* | `openlex__zhlaw_get_law_metadata` |

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

### Designentscheidung: Nur Tools (keine MCP Resources)

Alle 8 Endpunkte werden als **Tools** statt als MCP Resources bereitgestellt. Begründung:

- Jeder Abruf ist **parametrisch** — Abfragen, Abkürzungen und Artikelnummern variieren pro Aufruf. Statische Resources (eine URI pro Dokument) bilden das nicht natürlich ab.
- Der Korpus umfasst **974 Gesetze × viele Artikel** — jede einzeln als Resource-URI zu registrieren würde eine unpraktikabel grosse Resource-Liste erzeugen.
- MCP-Resource-Templates (`zhlex://laws/{sr_number}`) sind eine künftige Option für Phase 2, falls Clients von Resource-Caching oder Subscriptions profitieren.

### Skalierungs-Einschränkungen

Der Streamable-HTTP-Transport hält den Session-State **prozessintern** (FastMCP-Default). Das hat zwei Konsequenzen:

- **Nur eine Instanz** — horizontale Skalierung (mehrere Replicas) bricht aktive Sessions, da es keinen geteilten Session-Store (Redis, Durable Objects etc.) gibt.
- **Kein Sticky-Session-LB nötig (heute)** — ein Single-Replica-Render-Deployment leitet alle Anfragen naturgemäss an einen Prozess.

Vor der Skalierung über eine Instanz hinaus: entweder einen geteilten Session-Store ergänzen **oder** den Edge-Load-Balancer so konfigurieren, dass er anhand des Headers `Mcp-Session-Id` mit einer Stick-Table und passender TTL routet.

---

## MCP-Protokollversion

| Element | Wert |
|---------|------|
| **Unterstützte Protokollversion** | `2025-11-25` |
| **SDK** | `mcp[cli] >= 1.3.0` (FastMCP) |
| **Verankert in** | `src/openlex_mcp/server.py` — Konstante `MCP_PROTOCOL_VERSION` |

### Update-Politik

1. Wird `mcp` aktualisiert (via Dependabot-PR), die Protokollversion in den SDK-Release-Notes prüfen.
2. Ändert sich die Protokollversion, `MCP_PROTOCOL_VERSION` in `server.py` aktualisieren, `docs/tool-hashes.json` neu generieren (`PYTHONPATH=src python scripts/gen_tool_hashes.py > docs/tool-hashes.json`) und die Änderung in `CHANGELOG.md` vermerken.
3. Vor dem Merge `pytest tests/ -m "not live"` ausführen, um die Kompatibilität zu bestätigen.

---

## Projektstruktur

```
openlex-mcp/
├── src/openlex_mcp/
│   ├── __init__.py              # Package
│   ├── __main__.py              # Einstiegspunkt für python -m
│   ├── server.py                # 8 MCP Tool-Definitionen (FastMCP) + Settings
│   ├── responses.py             # Typisierte strukturierte Response-Envelopes (SDK-002)
│   ├── logging_config.py        # structlog JSON-Logging-Setup (OBS-003)
│   ├── net.py                   # SSRF-/Egress-gehärteter ausgehender HTTP
│   ├── api_client.py            # zh.ch HTTP-Client + Metadaten-Extraktion
│   ├── data_cache.py            # SQLite + FTS5 Cache-Management
│   └── law_parser.py            # Artikelextraktion aus Gesetzestexten
├── tests/                       # 89 Unit-Tests (Parser, Cache, Net, Tools…)
├── scripts/gen_tool_hashes.py   # Hash-Snapshot der Tool-Definitionen (SEC-022)
├── docs/                        # network-egress, secret-management, tool-hashes
├── .github/workflows/ci.yml     # GitHub Actions (Python 3.11/3.12/3.13)
├── .github/dependabot.yml       # Wöchentliche Dependency-PRs (ARCH-012)
├── Dockerfile                   # Gehärteter Multi-Stage-Build (SEC-007/SCALE-004)
├── compose.yml                  # Ressourcenlimits für lokale Tests (SCALE-006)
├── pyproject.toml
├── claude_desktop_config.json   # Beispiel-Konfiguration für Claude Desktop
├── CHANGELOG.md
├── ROADMAP.md                   # Phasenplan + Register akzeptierter Risiken
├── CONTRIBUTING.md              # Beitragsleitfaden (Englisch)
├── CONTRIBUTING.de.md           # Beitragsleitfaden (Deutsch)
├── SECURITY.md                  # Sicherheitsrichtlinie (Englisch)
├── SECURITY.de.md               # Sicherheitsrichtlinie (Deutsch)
├── LICENSE
├── README.md                    # Englische Hauptversion
└── README.de.md                 # Diese Datei (Deutsch)
```

### Tool-Ausgabeformat

Alle Tools liefern ein **strukturiertes Response-Envelope** (kein Markdown-Text), sodass MCP-Clients `structuredContent` erhalten, das sie direkt parsen können:

```jsonc
{
  "source": "Kanton Zürich Rechtssammlung — HuggingFace … & zh.ch",
  "provenance": "cache",          // cache | live | parser | cache+parser | none
  "result_type": "law_summaries", // law_summaries | law_detail | articles | metadata | cache_status
  "count": 2,
  "message": null,                // menschenlesbarer Hinweis für leere/Randfälle
  "results": [ /* typisierte Items */ ]
}
```

---

## Bekannte Einschränkungen

- **HuggingFace-Datensatz:** Das Feld `html_content` ist unzuverlässig (Inhalte zwischen Gesetzen vertauscht); der Server nutzt stattdessen `pdf_content`, das korrekt ist, aber PDF-Extraktionsartefakte aufweist (Silbentrennung, Layout)
- **Artikel-Parser:** PDF-Textextraktion verschmelzt manchmal Artikelgrenzen; komplex verschachtelte Artikel werden nicht immer perfekt geparst
- **Erststart:** Erster Start benötigt ~25s zum Herunterladen und Indexieren von 974 Gesetzen von HuggingFace (~38 MB SQLite-Datenbank)
- **zh.ch-Metadaten:** Keine offizielle API; Metadaten-Extraktion basiert auf HTML-Mustern, die sich ändern können
- **Offline-Modus:** Volltextsuche funktioniert offline nach Erststart; Live-Metadaten benötigen Internet

---

## Sicherheit & Limiten

| Aspekt | Details |
|--------|---------|
| **Zugriff** | Nur lesend (`readOnlyHint: true`) — der Server kann keine Daten ändern oder löschen |
| **Personendaten** | Keine Personendaten — alle Quellen sind aggregierte, öffentliche Gesetzestexte |
| **Rate Limits** | Eingebaute Limits pro Abfrage (max. 50 Suchergebnisse, 5000 Zeichen Inhaltsvorschau) |
| **Timeout** | 30 Sekunden pro HTTP-Aufruf an zh.ch |
| **Egress** | Ausgehende Anfragen sind auf eine Allow-List beschränkt (`www.zh.ch` über HTTPS, plus der nur per HTTP erreichbare Legacy-Permalink-Host `www.zhlex.zh.ch`), mit SSRF-IP-Sperre und DNS-Pinning — siehe [docs/network-egress.md](docs/network-egress.md) |
| **Authentifizierung** | Kein API-Schlüssel erforderlich — HuggingFace-Datensatz ist öffentlich, zh.ch ist offen |
| **Sicherheitsprofil (Lethal Trifecta)** | Score **1 / 3**: nur öffentliche Daten (keine privaten/sensiblen Daten) ✓ · ausschliesslich GET-Egress zu `*.zh.ch` — kein POST, keine Webhooks, keine E-Mail ✓ · keine Codeausführung ✓. Konstruktionsbedingt sicher. |
| **Session-Handling** | `Mcp-Session-Id` wird vom MCP-SDK generiert und verwaltet (kryptografisch sichere UUIDs). Keine Bindung an eine Benutzeridentität — `auth_model=none` ist für öffentliche, nur lesbare Daten korrekt. Falls jemals eine Authentifizierung hinzukommt, Sessions vor dem Deployment an den validierten OAuth-`sub`-Claim binden. |
| **Geheimnisse** | Keine gehalten — alle Datenquellen sind öffentlich. Siehe [docs/secret-management.md](docs/secret-management.md). |
| **Lizenzen** | Gesetzesdaten: CC-BY-SA 4.0 ([rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation)); zh.ch-Metadaten: öffentlich |
| **Nutzungsbedingungen** | Unterliegt den Nutzungsbedingungen von [HuggingFace](https://huggingface.co/terms-of-service) und [Kanton Zürich](https://www.zh.ch/de/rechtliche-hinweise.html) |
| **Haftungsausschluss** | Dieser Server stellt Gesetzestexte ausschliesslich zu Informationszwecken bereit — er ersetzt keine Rechtsberatung |

Um eine Sicherheitslücke zu melden, siehe die [Sicherheitsrichtlinie](SECURITY.de.md).

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

## Roadmap

Siehe [ROADMAP.md](ROADMAP.md)

---

## Mitwirken

Siehe [CONTRIBUTING.de.md](CONTRIBUTING.de.md)

---

## Sicherheit

Siehe [SECURITY.de.md](SECURITY.de.md)

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
