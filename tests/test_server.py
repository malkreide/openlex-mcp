"""Unit-Tests für die Server-Tools und das Netzwerk-Binding (SEC-016)."""
from __future__ import annotations

import logging

import pytest
from mcp.server.fastmcp.exceptions import ToolError

import openlex_mcp.server as srv

# ---------------------------------------------------------------------------
# Tool-Handler (Cache via Fixture injiziert)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_laws_returns_hits(server_with_cache):
    out = await srv.zhlaw_search_laws(srv.SearchLawsInput(query="Elternrat"))
    assert "412.100" in out
    assert "Quelle" in out  # SOURCE_FOOTER


@pytest.mark.asyncio
async def test_search_laws_no_hits_gives_tips(server_with_cache):
    out = await srv.zhlaw_search_laws(srv.SearchLawsInput(query="Raumfahrt"))
    assert "Keine Gesetze gefunden" in out


@pytest.mark.asyncio
async def test_get_law_by_abbreviation(server_with_cache):
    out = await srv.zhlaw_get_law(srv.GetLawInput(identifier="VSG"))
    assert "Volksschulgesetz" in out


@pytest.mark.asyncio
async def test_get_law_not_found(server_with_cache):
    out = await srv.zhlaw_get_law(srv.GetLawInput(identifier="XYZ"))
    assert "nicht gefunden" in out


@pytest.mark.asyncio
async def test_get_article_extracts(server_with_cache):
    out = await srv.zhlaw_get_article(
        srv.GetArticleInput(law_identifier="VSG", article_number="28")
    )
    assert "Art. 28" in out
    assert "Elternrat" in out


@pytest.mark.asyncio
async def test_list_laws_active_only(server_with_cache):
    out = await srv.zhlaw_list_laws(srv.ListLawsInput(active_only=True))
    assert "412.100" in out
    assert "999.9" not in out  # aufgehoben


@pytest.mark.asyncio
async def test_search_articles(server_with_cache):
    out = await srv.zhlaw_search_articles(
        srv.SearchArticlesInput(law_identifier="VSG", query="Eltern")
    )
    assert "Art. 28" in out


# ---------------------------------------------------------------------------
# Input-Validation (SEC-018)
# ---------------------------------------------------------------------------


def test_search_input_rejects_unknown_field():
    with pytest.raises(Exception):
        srv.SearchLawsInput(query="x", unknown="y")


def test_search_input_rejects_out_of_range_limit():
    with pytest.raises(Exception):
        srv.SearchLawsInput(query="x", limit=999)


def test_metadata_input_rejects_bad_sr_number():
    with pytest.raises(Exception):
        srv.GetLawMetadataInput(sr_number="not-a-number")


def test_protocol_error_missing_required_arg_rejected():
    # OBS-001 (protocol-error path): malformed args are rejected at the schema
    # boundary before any tool logic runs (the lowlevel server turns this into
    # an isError result rather than executing the tool).
    with pytest.raises(Exception):
        srv.GetArticleInput(law_identifier="VSG")  # article_number fehlt


# ---------------------------------------------------------------------------
# OBS-001 / OBS-002: execution errors are masked isError results, not leaks
# ---------------------------------------------------------------------------


def _boom(*_args, **_kwargs):
    raise RuntimeError("DB locked at /secret/path/zhlex_cache.db")


@pytest.mark.asyncio
async def test_execution_error_raises_masked_toolerror(server_with_cache, cache, monkeypatch):
    monkeypatch.setattr(cache, "search_fulltext", _boom)
    with pytest.raises(ToolError) as excinfo:
        await srv.zhlaw_search_laws(srv.SearchLawsInput(query="Eltern"))
    msg = str(excinfo.value)
    # No internals reach the LLM-facing error message.
    assert "secret" not in msg.lower()
    assert "RuntimeError" not in msg
    assert "DB locked" not in msg
    # But the actionable context is preserved.
    assert "Volltextsuche" in msg


@pytest.mark.asyncio
async def test_execution_error_logs_original_to_server_log(
    server_with_cache, cache, monkeypatch, caplog
):
    monkeypatch.setattr(cache, "search_fulltext", _boom)
    with caplog.at_level(logging.ERROR, logger="openlex_mcp"):
        with pytest.raises(ToolError):
            await srv.zhlaw_search_laws(srv.SearchLawsInput(query="Eltern"))
    # The original error is captured in the server log (with traceback), only.
    assert any("fehlgeschlagen" in r.message for r in caplog.records)
    assert any(r.exc_info is not None for r in caplog.records)


@pytest.mark.asyncio
async def test_not_found_is_a_normal_result_not_an_error(server_with_cache):
    # ARCH-003 / OBS-001: a legitimate "no results" is a normal result with
    # guidance, NOT an isError — so it must not raise.
    out = await srv.zhlaw_get_law(srv.GetLawInput(identifier="DOESNOTEXIST"))
    assert "nicht gefunden" in out


# ---------------------------------------------------------------------------
# SEC-016: 0.0.0.0-Binding-Prevention
# ---------------------------------------------------------------------------


def test_default_http_host_is_localhost(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.setattr(srv.sys, "argv", ["openlex-mcp", "--http"])
    host, port = srv._resolve_http_host_port()
    assert host == "127.0.0.1"
    assert port == 8000


def test_env_overrides_host_and_port(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9001")
    monkeypatch.setattr(srv.sys, "argv", ["openlex-mcp", "--http"])
    host, port = srv._resolve_http_host_port()
    assert host == "0.0.0.0"
    assert port == 9001


def test_cli_arg_overrides_env(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setattr(
        srv.sys, "argv", ["openlex-mcp", "--http", "--host", "127.0.0.1", "--port", "7000"]
    )
    host, port = srv._resolve_http_host_port()
    assert host == "127.0.0.1"
    assert port == 7000


def test_warn_on_public_binding_outside_container(monkeypatch, caplog):
    monkeypatch.setattr(srv, "_in_container", lambda: False)
    with caplog.at_level(logging.WARNING):
        srv._warn_on_public_binding("0.0.0.0")
    assert any("NeighborJack" in r.message for r in caplog.records)


def test_no_warning_for_localhost(monkeypatch, caplog):
    monkeypatch.setattr(srv, "_in_container", lambda: False)
    with caplog.at_level(logging.WARNING):
        srv._warn_on_public_binding("127.0.0.1")
    assert not caplog.records


def test_no_warning_when_in_container(monkeypatch, caplog):
    monkeypatch.setattr(srv, "_in_container", lambda: True)
    with caplog.at_level(logging.WARNING):
        srv._warn_on_public_binding("0.0.0.0")
    assert not caplog.records
