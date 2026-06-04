# Mitwirken bei openlex-mcp

[🇬🇧 English Version](CONTRIBUTING.md)

Vielen Dank für dein Interesse an einem Beitrag! Dieser Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Issues melden

Nutze [GitHub Issues](https://github.com/malkreide/openlex-mcp/issues), um Fehler zu melden oder Funktionen vorzuschlagen.

Bitte gib an:
- Python-Version und Betriebssystem
- Vollständige Fehlermeldung oder Beschreibung des unerwarteten Verhaltens
- Schritte zur Reproduktion

Für **Sicherheitslücken** folge bitte der [Sicherheitsrichtlinie](SECURITY.de.md), anstatt ein öffentliches Issue zu eröffnen.

---

## Pull Requests

1. Repository forken
2. Feature-Branch erstellen: `git checkout -b feat/dein-feature`
3. Änderungen vornehmen und Tests ergänzen
4. Sicherstellen, dass alle Tests bestehen: `PYTHONPATH=src pytest tests/ -m "not live"`
5. Mit [Conventional Commits](https://www.conventionalcommits.org/) committen: `feat: add new tool`
6. Pushen und einen Pull Request gegen `main` eröffnen

---

## Code-Stil

- Python 3.11+
- [Ruff](https://github.com/astral-sh/ruff) für Linting und Formatierung
- Type Hints für alle öffentlichen Funktionen erforderlich
- Tests für neue Tools erforderlich
- Den bestehenden FastMCP- / Pydantic-v2-Mustern in `server.py` folgen

---

## Datenquellen

Dieser Server nutzt zwei offene Datenquellen — alle ohne Authentifizierung:

| Quelle | Dokumentation |
|--------|---------------|
| HuggingFace `rcds/swiss_legislation` | [huggingface.co/datasets/rcds/swiss_legislation](https://huggingface.co/datasets/rcds/swiss_legislation) |
| zh.ch ZH-Lex | [zh.ch Gesetzessammlung](https://www.zh.ch/de/politik-staat/gesetze-beschluesse/gesetzessammlung.html) |

Beim Hinzufügen neuer Datenquellen gilt das **No-Auth-First**-Prinzip: ausschliesslich offene, authentifizierungsfreie Endpunkte verwenden.

---

## Lizenz

Mit deinem Beitrag erklärst du dich damit einverstanden, dass deine Beiträge unter der [MIT-Lizenz](LICENSE) lizenziert werden.
