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


# ---------------------------------------------------------------------------
# Die 24-Stunden-Grenze
#
# Sie steht an drei Stellen als Zusage — im Default von `is_fresh`, im
# Docstring von `load_from_huggingface` («< 24h alt») und in der
# Tool-Beschreibung, die das Modell liest («Cache <24h alt»). Gemessen hat sie
# bisher niemand. Ein verschobener Default waere still: Der Cache lieferte
# laenger oder kuerzer aus als angekuendigt, und kein Test haette widersprochen.
#
# Geprueft wird mit Abstand zur Grenze, nicht auf ihr. Der Zeitstempel wird auf
# ganze Sekunden abgeschnitten und zwischen Setzen und Messen vergeht Zeit —
# beides vergroessert das gemessene Alter. Ein Test genau bei 24.0 h haenge
# damit an einer Rundung statt an der Zusage. Ob die Grenze `<` oder `<=` ist,
# laesst sich aus demselben Grund nicht sinnvoll pruefen und wird hier auch
# nicht behauptet.
# ---------------------------------------------------------------------------


def test_ein_cache_knapp_unter_24h_ist_frisch(cache, mark_fresh):
    mark_fresh(cache, age_hours=23.9)
    assert cache.is_fresh() is True


def test_ein_cache_knapp_ueber_24h_ist_nicht_mehr_frisch(cache, mark_fresh):
    mark_fresh(cache, age_hours=24.1)
    assert cache.is_fresh() is False


def test_max_age_hours_verschiebt_die_grenze(cache, mark_fresh):
    """Der Parameter wird benutzt, nicht bloss entgegengenommen.

    Dasselbe Alter, zwei Schranken, zwei Antworten — ein `is_fresh`, das den
    Default hartverdrahtet, faellt hier auf.
    """
    mark_fresh(cache, age_hours=2.0)
    assert cache.is_fresh(max_age_hours=1) is False
    assert cache.is_fresh(max_age_hours=3) is True
