"""Unit-Tests für den Gesetzes-Parser (reine Funktionen, offline)."""
from __future__ import annotations

from openlex_mcp.law_parser import (
    clean_text,
    extract_article,
    format_article,
    format_article_list,
    parse_law_text,
    search_in_articles,
)

SAMPLE = (
    "Art. 1 Zweck\n"
    "Dieses Gesetz regelt die Volksschule.\n\n"
    "Art. 28 Elternmitwirkung\n"
    "Die Eltern wirken mit. Ein Elternrat kann gebildet werden.\n\n"
    "Art. 28a Ergänzung\n"
    "Eine ergänzende Bestimmung."
)


def test_clean_text_strips_html_and_entities():
    raw = "<p>Hallo&nbsp;&amp;&nbsp;Welt</p>\t\n\n\n\nEnde"
    out = clean_text(raw)
    assert "<p>" not in out
    assert "&nbsp;" not in out
    assert "&" in out
    # Mehr als zwei aufeinanderfolgende Leerzeilen werden normalisiert.
    assert "\n\n\n" not in out


def test_parse_law_text_extracts_all_articles():
    articles = parse_law_text(SAMPLE)
    numbers = [a.number for a in articles]
    assert "1" in numbers
    assert "28" in numbers
    assert "28a" in numbers


def test_parse_law_text_empty_returns_empty_list():
    assert parse_law_text("Kein Artikel hier drin.") == []


def test_extract_article_exact_match():
    art = extract_article(SAMPLE, "28")
    assert art is not None
    assert art.number == "28"
    assert "Elternrat" in art.content


def test_extract_article_letter_suffix_is_distinct():
    art = extract_article(SAMPLE, "28a")
    assert art is not None
    assert art.number == "28a"
    assert "ergänzende" in art.content.lower()


def test_extract_article_missing_returns_none():
    assert extract_article(SAMPLE, "999") is None


# Einzeiliger PDF-Extrakt ohne separate Titelzeile: § 1 läuft direkt in den
# Absatztext, inkl. Querverweis "gemäss §§ 33". Früher verschluckte das
# Titel-Feld den gesamten Fliesstext und content blieb leer (Live-Test-Regression).
SINGLE_LINE = (
    "412.100 Volksschulgesetz (VSG)  "
    "§ 1.  1 Dieses Gesetz regelt die Bildung und Erziehung in der "
    "Volks- schule einschliesslich der Sonderschulung gemäss  §§ 33–36.  "
    "2 Es gilt sinngemäss auch für Privatschulen.  "
    "§ 2.  Die Volksschule umfasst Kindergarten und Primarstufe."
)


def test_extract_article_single_line_pdf_has_content():
    art = extract_article(SINGLE_LINE, "1")
    assert art is not None
    assert art.number == "1"
    # Der Inhalt darf nicht leer sein und muss den Fliesstext enthalten.
    assert art.content, "Article content must not be empty"
    assert "Dieses Gesetz regelt" in art.content


def test_extract_article_single_line_pdf_second_article():
    art = extract_article(SINGLE_LINE, "2")
    assert art is not None
    assert art.number == "2"
    assert "Volksschule umfasst" in art.content


def test_search_in_articles_finds_term():
    hits = search_in_articles(SAMPLE, "Elternrat")
    assert len(hits) == 1
    assert hits[0].number == "28"


def test_search_in_articles_case_insensitive_no_match():
    assert search_in_articles(SAMPLE, "Steuern") == []


def test_format_article_includes_number_and_law_name():
    art = extract_article(SAMPLE, "1")
    out = format_article(art, "VSG")
    assert "Art. 1" in out
    assert "VSG" in out


def test_format_article_list_empty():
    assert format_article_list([]) == "Keine Artikel gefunden."
