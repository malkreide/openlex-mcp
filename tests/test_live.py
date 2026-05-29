"""Live-Tests — echte API-Calls (nightly + manuell, nie in CI).

Ausführen:  PYTHONPATH=src pytest -m live -v
Überspringen in CI:  pytest tests/ -m "not live"  (see ci.yml)

Deckt alle 8 MCP-Tools ab. Requires real network access:
  - HuggingFace rcds/swiss_legislation (dataset download, ~25 s)
  - www.zh.ch (HTML scraping, 1 HTTP request)
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

import openlex_mcp.api_client as api_client
import openlex_mcp.server as srv
from openlex_mcp.data_cache import LawCache


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Load the full HuggingFace dataset once; inject into srv._cache.

    force=True guarantees last_update is written so update_cache(force=False)
    returns "cache_fresh" rather than triggering a second download.
    """
    db_dir = tmp_path_factory.mktemp("live_db")
    cache = LawCache(db_dir=db_dir)
    result = cache.load_from_huggingface(force=True)
    assert result.get("status") == "ok", f"HuggingFace load failed: {result}"

    original_cache = srv._cache
    srv._cache = cache
    yield srv
    srv._cache = original_cache


@pytest.fixture
async def _http_client():
    """Create and properly close a real httpx.AsyncClient for live HTTP tests.

    Runs after the conftest autouse _reset_shared_http_client (which sets
    ac._client = None). Creates a fresh client, yields, then closes it to
    avoid ResourceWarning from unclosed transports.
    """
    client = api_client.get_client()
    yield client
    await api_client.aclose_client()


# ---------------------------------------------------------------------------
# Tool 1 — zhlaw_search_laws
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_search_laws(live_server):
    resp = await srv.zhlaw_search_laws(srv.SearchLawsInput(query="Volksschule"))
    assert resp.result_type == "law_summaries"
    assert resp.count >= 1
    assert resp.results, "Expected at least one result"
    assert any("412" in (r.sr_number or "") for r in resp.results)


# ---------------------------------------------------------------------------
# Tool 2 — zhlaw_get_law
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_get_law(live_server):
    resp = await srv.zhlaw_get_law(srv.GetLawInput(identifier="VSG"))
    assert resp.result_type == "law_detail"
    assert resp.count == 1
    law = resp.results[0]
    assert law.sr_number == "412.100"
    assert "Volksschul" in law.title
    assert law.abbreviation == "VSG"
    assert law.is_active is True


# ---------------------------------------------------------------------------
# Tool 3 — zhlaw_get_article
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_get_article(live_server):
    resp = await srv.zhlaw_get_article(
        srv.GetArticleInput(law_identifier="VSG", article_number="1")
    )
    assert resp.result_type == "articles"
    assert resp.count == 1
    art = resp.results[0]
    assert art.number == "1"
    assert art.content, "Article content must not be empty"
    assert art.law in ("VSG", "412.100")


# ---------------------------------------------------------------------------
# Tool 4 — zhlaw_list_laws
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_list_laws(live_server):
    resp = await srv.zhlaw_list_laws(srv.ListLawsInput(active_only=True, limit=50))
    assert resp.result_type == "law_summaries"
    assert resp.count >= 50
    sr_numbers = {r.sr_number for r in resp.results}
    assert any(sr and sr.startswith("4") for sr in sr_numbers)


# ---------------------------------------------------------------------------
# Tool 5 — zhlaw_find_education_laws
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_find_education_laws(live_server):
    resp = await srv.zhlaw_find_education_laws(
        srv.FindEducationLawsInput(query="Volksschule")
    )
    assert resp.result_type == "law_summaries"
    assert resp.count >= 1
    for law in resp.results:
        if law.sr_number:
            assert law.sr_number.startswith("412"), (
                f"Expected 412.x prefix, got {law.sr_number}"
            )


# ---------------------------------------------------------------------------
# Tool 6 — zhlaw_search_articles
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_search_articles(live_server):
    resp = await srv.zhlaw_search_articles(
        srv.SearchArticlesInput(law_identifier="VSG", query="Schule")
    )
    assert resp.result_type == "articles"
    assert resp.count >= 1
    for art in resp.results:
        assert "schule" in art.content.lower() or "schule" in (art.title or "").lower()


# ---------------------------------------------------------------------------
# Tool 7 — zhlaw_get_law_metadata  (live HTTP to zh.ch)
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_get_law_metadata(live_server, _http_client):
    resp = await srv.zhlaw_get_law_metadata(
        srv.GetLawMetadataInput(sr_number="412.100")
    )
    assert resp.result_type == "metadata"
    assert resp.count == 1
    item = resp.results[0]
    assert item.sr_number == "412.100"
    assert item.found is True, f"Expected found=True, got error: {item.error}"
    assert item.page_title is not None, "Expected page_title from zh.ch"
    assert item.url is not None
    assert item.cached_title is not None
    assert "Volksschul" in item.cached_title


# ---------------------------------------------------------------------------
# Tool 8 — zhlaw_update_cache
# ---------------------------------------------------------------------------


@pytest.mark.live
async def test_live_update_cache(live_server):
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.warning = AsyncMock()
    ctx.report_progress = AsyncMock()

    resp = await srv.zhlaw_update_cache(ctx, srv.UpdateCacheInput(force=False))

    assert resp.result_type == "cache_status"
    assert resp.count == 1
    # The module fixture used force=True → cache is fresh (<24 h old)
    # → update_cache(force=False) must return "cache_fresh"
    assert resp.results[0].status == "cache_fresh", (
        f"Expected cache_fresh, got {resp.results[0].status}: {resp.results[0].detail}"
    )
    ctx.info.assert_called()
    assert ctx.report_progress.call_count >= 2
