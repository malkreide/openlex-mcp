# Sicherheitsrichtlinie

[🇬🇧 English Version](SECURITY.md)

Dieser Server ist Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide).

---

## Unterstützte Versionen

Nur die jeweils neueste veröffentlichte Version erhält Sicherheitsupdates.

| Version | Unterstützt |
|---------|-------------|
| 0.2.x   | ✅          |
| < 0.2   | ❌          |

---

## Eine Sicherheitslücke melden

Bitte melde Sicherheitslücken **vertraulich** — eröffne kein öffentliches GitHub-Issue.

- Nutze [GitHub Security Advisories](https://github.com/malkreide/openlex-mcp/security/advisories/new) (bevorzugt), oder
- sende eine E-Mail an **hayal.oezkan@gmail.com** mit dem Betreff `SECURITY: openlex-mcp`.

Bitte gib an:
- Eine Beschreibung der Sicherheitslücke und ihrer möglichen Auswirkungen
- Schritte zur Reproduktion (nach Möglichkeit ein Proof of Concept)
- Betroffene Version(en) und Umgebung

Du erhältst innerhalb von **5 Werktagen** eine erste Rückmeldung. Sobald ein Fix
veröffentlicht ist, nennen wir dich gerne im Advisory, sofern du nicht anonym
bleiben möchtest.

---

## Sicherheitsprofil

`openlex-mcp` ist ein **nur lesender** MCP-Server **ohne Authentifizierung** über
öffentliche Open Data. Er ist konstruktionsbedingt risikoarm.

| Aspekt | Details |
|--------|---------|
| **Zugriff** | Nur lesend (`readOnlyHint: true`) — der Server kann keine Daten ändern oder löschen |
| **Personendaten** | Keine — alle Quellen sind aggregierte, öffentliche Gesetzestexte |
| **Geheimnisse** | Keine gehalten — alle Datenquellen sind öffentlich (siehe [docs/secret-management.md](docs/secret-management.md)) |
| **Authentifizierung** | Kein API-Schlüssel erforderlich (`auth_model=none`) |
| **Lethal Trifecta** | Score **1 / 3**: nur öffentliche Daten (keine privaten/sensiblen Daten) ✓ · ausschliesslich GET-Egress zu `*.zh.ch` — kein POST, keine Webhooks, keine E-Mail ✓ · keine Codeausführung ✓ |

### Härtung des Netzwerk-Egress

Ausgehende Anfragen des HTTP-Clients werden durch eine Allow-List auf Code-Ebene
([`src/openlex_mcp/net.py`](src/openlex_mcp/net.py)) eingeschränkt, durchgesetzt
vor jeder Anfrage **und jedem Redirect-Hop**:

- **HTTPS standardmässig** — `http://` ist nur für den Legacy-Permalink-Host
  `www.zhlex.zh.ch` erlaubt
- **Host-Allow-List** — nur `www.zh.ch` und `www.zhlex.zh.ch`
- **SSRF-IP-Sperre** — private / Loopback- / Link-Local- / Carrier-Grade-NAT-Bereiche
  sowie die Cloud-Metadaten-Adresse `169.254.169.254` werden abgewiesen
- **DNS-Pinning** — Verbindungen werden auf die validierte IP gepinnt, um das
  TOCTOU- / DNS-Rebinding-Zeitfenster zu schliessen

Siehe [docs/network-egress.md](docs/network-egress.md) für die vollständige
Richtlinie und die empfohlene Defense-in-Depth auf Netzwerkebene.

### Netzwerk-Binding

Der HTTP-Transport bindet standardmässig an **`127.0.0.1`** (nur localhost).
Binde ausserhalb eines Containers niemals an `0.0.0.0` — das macht den Server im
lokalen Netzwerk erreichbar (NeighborJack-Risiko). Für Container-/Cloud-Deployments
setze `MCP_HOST=0.0.0.0` explizit; ausserhalb eines erkannten Containers
protokolliert der Server eine Warnung.

### Sessions

`Mcp-Session-Id`-Werte werden vom MCP-SDK generiert und verwaltet
(kryptografisch sichere UUIDs). Es gibt keine Bindung an eine Benutzeridentität,
was für öffentliche, nur lesbare Daten korrekt ist. Falls jemals eine
Authentifizierung hinzugefügt wird, müssen Sessions vor dem Deployment an den
validierten OAuth-`sub`-Claim gebunden werden.

---

## Geltungsbereich

Diese Richtlinie deckt den Code des `openlex-mcp`-Servers ab. Sicherheitslücken in
vorgelagerten Datenquellen (HuggingFace, zh.ch) oder in Drittanbieter-Abhängigkeiten
sollten den jeweiligen Maintainern gemeldet werden; Abhängigkeits-Updates werden
über wöchentliche Dependabot-PRs verfolgt.
