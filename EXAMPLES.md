# Use Cases & Examples — openlex-mcp

Praxisnahe Anfragen nach Zielgruppe. openlex-mcp bietet KI-nativen Zugriff auf die gesamte Zürcher Gesetzessammlung (ZH-Lex, ~970 kantonale Gesetze): Volltextsuche, Artikel-Extraktion und spezialisierte Bildungsrecht-Tools. **Kein API-Key nötig** — alle Daten unter offenen Lizenzen (Volltext aus HuggingFace, gecacht; Live-Metadaten von zh.ch).

## 🏫 Bildung & Schule

**«Was sagt das Volksschulgesetz zur Elternmitwirkung? Zeig mir Art. 55 VSG.»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_search_articles(law_identifier="VSG", query="Elternrat")`
→ `openlex__zhlaw_get_article(law_identifier="VSG", article_number="55")`
Warum nützlich: Lehrpersonen und Schulleitungen erhalten den exakten Gesetzeswortlaut zur Elternmitwirkung, ohne PDFs durchsuchen zu müssen — direkt zitierfähig für Reglemente und Elterngespräche.

**«Welche Bildungsgesetze regeln Tagesstrukturen und Sonderpädagogik?»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_find_education_laws(query="Tagesstrukturen", limit=10)`
→ `openlex__zhlaw_find_education_laws(query="Sonderpädagogik", limit=10)`
Warum nützlich: Die Bildungsrecht-Schnellsuche durchsucht gezielt nur die Serie 412.x (Volksschule, Lehrpersonal, Sonderpädagogik) — schneller und präziser als die allgemeine Suche.

**«Gib mir eine Übersicht aller aktiven Bildungsgesetze des Kantons Zürich.»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_list_laws(sr_prefix="412", active_only=True, limit=50)`
Warum nützlich: Liefert eine strukturierte Liste (Titel, Abkürzung, LS-Nummer, Status) aller geltenden Bildungserlasse — ideal als Ausgangspunkt für Schulungen oder Reglementsrevisionen.

## 👨‍👩‍👧 Eltern & Schulgemeinde

**«Was genau ist das VSG und ist es noch in Kraft?»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_get_law(identifier="VSG", include_content=False)`
→ `openlex__zhlaw_get_law_metadata(sr_number="412.100")`
Warum nützlich: Eltern erhalten Titel, Abkürzung und den aktuellen Gültigkeitsstatus samt Live-Link zur offiziellen zh.ch-Fassung — verlässliche Grundlage statt Hörensagen.

**«In welchem Artikel steht, wie ein Elternrat gebildet wird?»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_search_articles(law_identifier="VSG", query="Elternrat")`
Warum nützlich: Die Schulgemeinde findet alle einschlägigen Artikel zu einem Stichwort innerhalb des relevanten Gesetzes — mit vollem Wortlaut, ohne juristische Vorkenntnisse.

## 🗳️ Bevölkerung & öffentliches Interesse

**«Welche Zürcher Gesetze regeln den Datenschutz?»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_search_laws(query="Datenschutz", limit=10)`
Warum nützlich: Volltextsuche über alle ~970 kantonalen Gesetze mit BM25-Relevanzranking — Bürgerinnen und Bürger finden die einschlägigen Erlasse zu einem Thema unabhängig vom Rechtsgebiet.

**«Ist die aktuell auf zh.ch publizierte Fassung dieses Gesetzes die neueste?»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_get_law_metadata(sr_number="412.100")`
Warum nützlich: Das einzige Tool mit Live-Abruf von zh.ch liefert Seitentitel, PDF-Links und Änderungsdatum — Transparenz über den aktuellen Rechtsstand.

## 🤖 KI-Interessierte & Entwickler:innen

**«Durchsuche alle Steuergesetze nach einem Begriff und hol dir den genauen Artikel.»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_search_laws(query="Eigenmietwert", sr_prefix="331", limit=10)`
→ `openlex__zhlaw_get_article(law_identifier="StG", article_number="21")`
Warum nützlich: Zeigt die typische Pipeline «Gesetz finden → Artikel extrahieren» mit FTS5-Volltextsuche und präziser Artikel-Extraktion — reproduzierbar und strukturiert (Response-Envelope statt Markdown).

**«Portfolio-Kombination: Gesetzestext + Rechtsprechung für eine vollständige Recherche.»**
**API-Key nötig:** Nein
→ `openlex__zhlaw_get_article(law_identifier="VSG", article_number="55")` (openlex-mcp: der Normtext)
→ danach in [`swiss-courts-mcp`](https://github.com/malkreide/swiss-courts-mcp) die zugehörige Rechtsprechung suchen
Warum nützlich: openlex-mcp liefert den geltenden Normtext, ein Rechtsprechungs-Server ergänzt die Gerichtspraxis — zusammen eine vollständige juristische Recherche zu einer Norm.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|---|---|---|
| Alle ~970 Zürcher Gesetze per Volltext (FTS5/BM25) durchsuchen | `openlex__zhlaw_search_laws` | Nein |
| Ein Gesetz per LS-Nummer oder Abkürzung abrufen (optional mit Volltext) | `openlex__zhlaw_get_law` | Nein |
| Gesetze nach Rechtsgebiet auflisten und filtern | `openlex__zhlaw_list_laws` | Nein |
| Gezielt im Bildungsrecht (Serie 412.x) suchen | `openlex__zhlaw_find_education_laws` | Nein |
| Einen bestimmten Artikel (z.B. Art. 28 VSG) extrahieren | `openlex__zhlaw_get_article` | Nein |
| Innerhalb eines Gesetzes alle Artikel zu einem Begriff finden | `openlex__zhlaw_search_articles` | Nein |
| Aktuelle Live-Metadaten von zh.ch (Gültigkeit, PDF-Links) abrufen | `openlex__zhlaw_get_law_metadata` | Nein |
| Den lokalen Gesetzes-Cache aus HuggingFace aktualisieren | `openlex__zhlaw_update_cache` | Nein |

---
🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_018dMqNTA37PLHvLRGriRDmq
