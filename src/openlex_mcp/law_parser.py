"""
Parser für Schweizer Gesetzestexte
===================================
Extrahiert einzelne Artikel, Paragraphen und Absätze aus
Gesetzestexten der Zürcher Rechtssammlung.

Schweizer Gesetzessystematik:
  - Art. 28 (oder § 28): Artikelnummer
  - ¹ ² ³ (Superscript-Ziffern): Absätze
  - lit. a, b, c: Buchstaben (Untergliederung)
  - Ziff. 1, 2, 3: Nummern (Untergliederung)
  - Art. 28a (mit Buchstabe): Einschub-Artikel

Erkennt sowohl HTML-Extrakte als auch Plain-Text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------


@dataclass
class Article:
    """Ein einzelner Gesetzesartikel."""
    number: str          # z.B. "28", "28a", "28bis"
    title: str = ""      # z.B. "Elternmitwirkung"
    content: str = ""    # Volltext des Artikels
    paragraphs: list[str] = field(default_factory=list)  # Absätze ¹²³


@dataclass
class ParsedLaw:
    """Ergebnis des Gesetzes-Parsings."""
    title: str = ""
    abbreviation: str = ""
    sr_number: str = ""
    articles: list[Article] = field(default_factory=list)
    preamble: str = ""   # Text vor dem ersten Artikel


# ---------------------------------------------------------------------------
# Regex-Patterns
# ---------------------------------------------------------------------------

# Artikel-Erkennung: "Art. 28", "Art. 28a", "§ 28", "Artikel 28bis"
# Unterstützt sowohl mehrzeilige Texte als auch einzeilige PDF-Extrakte
_ARTICLE_PATTERN = re.compile(
    r"(?:^|\n|\s{2,})"                     # Zeilenanfang oder Einrückung
    r"\s*"
    r"(?:Art\.?(?:ikel)?|§)\s*"            # "Art.", "Artikel", "§"
    r"(\d+[a-z]?(?:bis|ter|quater)?)"      # Nummer: 28, 28a, 28bis
    r"(?:\.\s*|\s+)"                        # Punkt oder Leerzeichen
    r"(.*?)(?=\s{2,}(?:Art|§)|\n|$)",       # Titel bis zum nächsten Artikel oder Zeilenende
    re.MULTILINE | re.IGNORECASE,
)

# Absatz-Erkennung: Superscript-Ziffern ¹²³⁴⁵⁶⁷⁸⁹
_PARAGRAPH_PATTERN = re.compile(
    r"([¹²³⁴⁵⁶⁷⁸⁹⁰]+)\s*(.+?)(?=\n[¹²³⁴⁵⁶⁷⁸⁹⁰]|\n\s*(?:Art|§)|\Z)",
    re.DOTALL,
)

# Alternative: nummerierte Absätze (1. 2. 3.) oder (1 2 3)
_NUMBERED_PARAGRAPH_PATTERN = re.compile(
    r"(?:^|\n)\s*(\d+)[.)]\s*(.+?)(?=\n\s*\d+[.)]|\n\s*(?:Art|§)|\Z)",
    re.DOTALL,
)

# HTML-Tags entfernen
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Mehrfache Leerzeilen normalisieren
_MULTI_NEWLINE = re.compile(r"\n{3,}")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def clean_text(text: str) -> str:
    """Bereinigt Gesetzestext: HTML-Tags entfernen, Whitespace normalisieren."""
    # HTML-Tags entfernen
    text = _HTML_TAG_PATTERN.sub(" ", text)
    # HTML-Entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&quot;", '"')
    # Non-breaking spaces und andere Unicode-Leerzeichen
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2003", " ")
    text = text.replace("\u2002", " ")
    # Tabs zu Leerzeichen
    text = text.replace("\t", " ")
    # Mehrfache Leerzeichen (aber Zeilenumbrüche erhalten)
    text = re.sub(r"[ ]+", " ", text)
    # Mehrfache Leerzeilen
    text = _MULTI_NEWLINE.sub("\n\n", text)
    return text.strip()


def _superscript_to_int(s: str) -> int:
    """Konvertiert Superscript-Ziffer zu int: ¹→1, ²→2, etc."""
    mapping = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
               "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}
    return int("".join(mapping.get(c, c) for c in s))


# ---------------------------------------------------------------------------
# Hauptparser
# ---------------------------------------------------------------------------


def parse_law_text(text: str) -> list[Article]:
    """Parst einen Gesetzestext und extrahiert alle Artikel.

    Args:
        text: Volltext des Gesetzes (HTML oder Plain-Text).

    Returns:
        Liste von Article-Objekten, sortiert nach Artikelnummer.
    """
    text = clean_text(text)

    # PDF-Texte haben oft keine Zeilenumbrüche vor Artikeln.
    # Füge Zeilenumbrüche vor "§ " und "Art. " ein für konsistentes Parsing.
    text = re.sub(r"(\S)\s+(§\s+\d)", r"\1\n\2", text)
    text = re.sub(r"(\S)\s+(Art\.?\s+\d)", r"\1\n\2", text)

    # Alle Artikel-Positionen finden
    matches = list(_ARTICLE_PATTERN.finditer(text))

    if not matches:
        return []

    articles: list[Article] = []

    for i, match in enumerate(matches):
        number = match.group(1).strip()
        title = match.group(2).strip().rstrip(".")

        # Artikeltext: von nach dem Titel bis zum nächsten Artikel
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        # Absätze extrahieren (Superscript-Ziffern)
        paragraphs: list[str] = []
        para_matches = list(_PARAGRAPH_PATTERN.finditer(content))

        if para_matches:
            for pm in para_matches:
                para_num = _superscript_to_int(pm.group(1))
                para_text = pm.group(2).strip()
                paragraphs.append(f"Abs. {para_num}: {para_text}")
        else:
            # Fallback: nummerierte Absätze
            num_matches = list(_NUMBERED_PARAGRAPH_PATTERN.finditer(content))
            for nm in num_matches:
                para_num = nm.group(1)
                para_text = nm.group(2).strip()
                paragraphs.append(f"Abs. {para_num}: {para_text}")

        articles.append(Article(
            number=number,
            title=title,
            content=content,
            paragraphs=paragraphs,
        ))

    return articles


def extract_article(text: str, article_number: str) -> Article | None:
    """Extrahiert einen bestimmten Artikel aus dem Gesetzestext.

    Args:
        text: Volltext des Gesetzes.
        article_number: Artikelnummer, z.B. '28', '28a', '28bis'.

    Returns:
        Article-Objekt oder None wenn nicht gefunden.
    """
    articles = parse_law_text(text)
    article_number = article_number.strip().lower()

    for article in articles:
        if article.number.lower() == article_number:
            return article

    return None


def search_in_articles(text: str, query: str) -> list[Article]:
    """Sucht in allen Artikeln eines Gesetzes nach einem Begriff.

    Args:
        text: Volltext des Gesetzes.
        query: Suchbegriff (case-insensitive).

    Returns:
        Liste von Artikeln, die den Begriff enthalten.
    """
    articles = parse_law_text(text)
    query_lower = query.lower()

    return [
        article for article in articles
        if (query_lower in article.content.lower()
            or query_lower in article.title.lower())
    ]


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------


def format_article(article: Article, law_name: str = "") -> str:
    """Formatiert einen Artikel als Markdown.

    Args:
        article: Das Article-Objekt.
        law_name: Optionaler Gesetzesname für den Header.

    Returns:
        Markdown-formatierter Artikeltext.
    """
    parts: list[str] = []

    header = f"### Art. {article.number}"
    if article.title:
        header += f"  {article.title}"
    if law_name:
        header += f" ({law_name})"
    parts.append(header)

    if article.paragraphs:
        parts.append("")
        for para in article.paragraphs:
            parts.append(f"- {para}")
    elif article.content:
        parts.append("")
        # Inhalt kürzen wenn sehr lang
        content = article.content
        if len(content) > 2000:
            content = content[:1997] + "..."
        parts.append(content)

    return "\n".join(parts)


def format_article_list(articles: list[Article], law_name: str = "") -> str:
    """Formatiert eine Liste von Artikeln als Markdown."""
    if not articles:
        return "Keine Artikel gefunden."

    parts: list[str] = []
    for article in articles:
        parts.append(format_article(article, law_name))

    return "\n\n".join(parts)
