"""Unit-Tests für den SQLite/FTS5-Cache (temporäre DB, offline)."""
from __future__ import annotations


def test_count_laws(cache):
    assert cache.count_laws() == 3


def test_get_by_sr_number(cache):
    law = cache.get_by_sr_number("412.100")
    assert law is not None
    assert law["abbreviation"] == "VSG"


def test_get_by_sr_number_missing(cache):
    assert cache.get_by_sr_number("000.0") is None


def test_get_by_abbreviation_is_case_insensitive(cache):
    assert cache.get_by_abbreviation("vsg")["sr_number"] == "412.100"


def test_search_fulltext_finds_term(cache):
    results = cache.search_fulltext("Elternrat")
    assert any(r["sr_number"] == "412.100" for r in results)


def test_search_fulltext_active_only_excludes_repealed(cache):
    results = cache.search_fulltext("aufgehoben", active_only=True)
    assert all(r["is_active"] == 1 for r in results)


def test_search_fulltext_sr_prefix_filter(cache):
    results = cache.search_fulltext("Volksschule", sr_prefix="412")
    assert results
    assert all(r["sr_number"].startswith("412") for r in results)


def test_list_laws_returns_total(cache):
    laws, total = cache.list_laws(active_only=False)
    assert total == 3
    assert len(laws) == 3


def test_list_laws_pagination(cache):
    laws, total = cache.list_laws(active_only=False, limit=1, offset=0)
    assert total == 3
    assert len(laws) == 1


def test_get_law_content(cache):
    content = cache.get_law_content("412.100")
    assert "Elternmitwirkung" in content


def test_is_fresh_false_when_no_update_recorded(cache):
    # populate() schreibt keinen last_update-Zeitstempel.
    assert cache.is_fresh() is False
