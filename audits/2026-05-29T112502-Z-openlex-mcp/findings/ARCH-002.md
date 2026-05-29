## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `openlex-mcp` |
| **Check-Reference** | `ARCH-002` |
| **PDF-Reference** | Sec 2.2 |
| **Audit-Datum** | 2026-05-29 |
| **Auditor** | claude-sonnet-4-6 |

### Observed Behavior

All 8 tool docstrings are 230–386 characters, well above the 50-character minimum, and contain substantive use-case context. However, no tool uses the structured XML-style tags (`<use_case>`, `<important_notes>`, `<example>`) required by the check for at least 80% of tools. There is also no negative disambiguation between similar tools (e.g., when to use `zhlaw_search_laws` vs `zhlaw_find_education_laws`).

Example (current):
```python
async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    Durchsucht Titel, Abkürzungen und Volltexte aller ~970 kantonalen Gesetze.
    Unterstützt FTS5-Syntax: AND, OR, NOT, Phrasensuche "...".
    Ergebnisse nach Relevanz sortiert (BM25-Algorithmus).

    Beispiele: 'Tagesschule', 'Datenschutz Gemeinde', 'Elternrat OR Elternmitwirkung'.
    """
```

### Expected Behavior

The check requires structured XML-style tags in at least 80% (7/8) of tools:
- `<use_case>` — when should the tool be used?
- `<important_notes>` — caveats, limitations, side-effects
- `<example>` — concrete sample inputs

```python
async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    <use_case>Wenn nach einem Rechtsbegriff in allen ~970 Zürcher Gesetzen gesucht
    werden soll. Für Bildungsrecht-spezifische Suche: openlex__zhlaw_find_education_laws
    verwenden (schneller, präziser für 412.x-Serie).</use_case>

    <important_notes>FTS5-Syntax: AND, OR, NOT, Phrasensuche "...". Ergebnisse nach
    BM25-Relevanz sortiert. Max 50 Treffer pro Aufruf. Sucht im Cache — Live-Daten
    via openlex__zhlaw_get_law_metadata.</important_notes>

    <example>query='Elternrat OR Elternmitwirkung', sr_prefix='412', limit=10</example>
    """
```

### Evidence

- `src/openlex_mcp/server.py`: 8 tool functions, none with `<use_case>`, `<important_notes>`, or `<example>` tags
- Grep: `grep -rE "<use_case>|<important_notes>|<example>" src/` returns no results
- Tool description lengths: 234–386 chars (all above minimum, but lacking structured tags)

### Risk Description

Without structured XML tags, the LLM must infer use-case boundaries from free-text descriptions. This increases the probability of the LLM choosing the wrong tool when multiple similar tools exist (e.g., `zhlaw_search_laws` vs `zhlaw_find_education_laws` vs `zhlaw_search_articles`). The gap is unlikely to cause failures but reduces disambiguation precision in ambiguous queries.

### Remediation

Add `<use_case>`, `<important_notes>`, and `<example>` tags to all 8 tool docstrings. The effort per tool is approximately 10–15 minutes.

```diff
  async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
      """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

-     Durchsucht Titel, Abkürzungen und Volltexte aller ~970 kantonalen Gesetze.
-     Unterstützt FTS5-Syntax: AND, OR, NOT, Phrasensuche "...".
-     Ergebnisse nach Relevanz sortiert (BM25-Algorithmus).
-
-     Beispiele: 'Tagesschule', 'Datenschutz Gemeinde', 'Elternrat OR Elternmitwirkung'.
+     <use_case>Allgemeine Suche in allen ~970 Zürcher Gesetzen nach Rechtsbegriffen.
+     Für Bildungsrecht (412.x) direkt: openlex__zhlaw_find_education_laws.
+     Für Artikel eines bekannten Gesetzes: openlex__zhlaw_search_articles.</use_case>
+
+     <important_notes>FTS5-Syntax: AND, OR, NOT, Phrasensuche "...". Max 50 Treffer.
+     Sucht im lokalen Cache — Aktualität via openlex__zhlaw_get_law_metadata prüfen.
+     sr_prefix filtert nach Rechtsgebiet (412=Bildung, 331=Steuern, 700=Bau).</important_notes>
+
+     <example>query='Elternrat OR Elternmitwirkung', sr_prefix='412', limit=10</example>
      """
```

### Effort Estimate

**S** — < 1 Tag. 8 tools × 15 Minuten ≈ 2 Stunden.

### Dependencies / Blockers

None.

### Verification After Fix

```bash
grep -rE "<use_case>|<important_notes>|<example>" src/openlex_mcp/server.py | wc -l
# Expected: >= 24 (3 tags × 8 tools)
```
