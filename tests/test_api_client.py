"""Unit-Tests für den zh.ch HTTP-Client (HTTP via respx gemockt)."""
from __future__ import annotations

import httpx
import pytest
import respx

from openlex_mcp import api_client


def test_build_zhlex_search_url_converts_dot_to_underscore():
    url = api_client.build_zhlex_search_url("412.100")
    assert url.startswith("https://")
    assert "erlass-412_100.html" in url


def test_build_zhlex_permalink_url_uses_ordnungsnummer():
    url = api_client.build_zhlex_permalink_url("412.100")
    assert url == "http://www.zhlex.zh.ch/Erlass.html?Open&Ordnr=412.100"


def test_build_lexfind_url_contains_query_and_canton():
    url = api_client.build_lexfind_url("412.100")
    assert "query=412.100" in url
    assert "canton=26" in url


def test_extract_metadata_from_html_title_and_pdf_links():
    html = (
        "<html><head><title>Kanton Zürich - Volksschulgesetz</title></head>"
        '<body><a href="/dam/vsg.pdf">PDF</a>'
        '<a href="https://example.ch/extern.pdf">Extern</a></body></html>'
    )
    meta = api_client._extract_metadata_from_html(html, "412.100")
    assert meta["page_title"] == "Volksschulgesetz"
    assert any("vsg.pdf" in link for link in meta["pdf_links"])
    assert "https://www.zh.ch/dam/vsg.pdf" in meta["pdf_links"]


def test_handle_error_maps_http_status():
    req = httpx.Request("GET", "https://www.zh.ch/x")
    resp = httpx.Response(404, request=req)
    err = httpx.HTTPStatusError("not found", request=req, response=resp)
    msg = api_client.handle_error(err, "Test")
    assert "404" in msg
    assert msg.startswith("Fehler bei Test")


def test_handle_error_timeout():
    msg = api_client.handle_error(httpx.TimeoutException("slow"), "Test")
    assert "Zeit" in msg or "erneut" in msg


def test_handle_error_masks_unexpected_exception():
    # OBS-002: the catch-all must not leak the exception type or message.
    msg = api_client.handle_error(
        RuntimeError("raw sql error: SELECT * FROM laws WHERE secret=1"), "Test"
    )
    assert "SELECT" not in msg
    assert "secret" not in msg
    assert "RuntimeError" not in msg
    assert "unerwartet" in msg.lower()


def _pin_resolver(ip: str):
    async def _resolve(_host: str, _port: int) -> list[str]:
        return [ip]

    return _resolve


@respx.mock
@pytest.mark.asyncio
async def test_fetch_zhlex_metadata_success(monkeypatch):
    ip = "203.0.113.10"
    monkeypatch.setattr(api_client.net, "_resolve", _pin_resolver(ip))
    url = api_client.build_zhlex_permalink_url("412.100")
    respx.get(api_client.net._pin_url(url, ip)).mock(
        return_value=httpx.Response(
            200,
            html="<title>Kanton Zürich - Volksschulgesetz</title>",
        )
    )
    meta = await api_client.fetch_zhlex_metadata("412.100")
    assert meta["found"] is True
    assert meta["page_title"] == "Volksschulgesetz"


@respx.mock
@pytest.mark.asyncio
async def test_fetch_zhlex_metadata_404_returns_not_found(monkeypatch):
    ip = "203.0.113.10"
    monkeypatch.setattr(api_client.net, "_resolve", _pin_resolver(ip))
    url = api_client.build_zhlex_permalink_url("000.0")
    respx.get(api_client.net._pin_url(url, ip)).mock(return_value=httpx.Response(404))
    meta = await api_client.fetch_zhlex_metadata("000.0")
    assert meta["found"] is False
    assert meta["sr_number"] == "000.0"


@pytest.mark.asyncio
async def test_fetch_blocked_when_host_resolves_to_metadata_ip(monkeypatch):
    # SEC-004: even the fixed host is refused if it resolves to a blocked IP.
    monkeypatch.setattr(api_client.net, "_resolve", _pin_resolver("169.254.169.254"))
    meta = await api_client.fetch_zhlex_metadata("412.100")
    assert meta["found"] is False
    assert "Egress" in meta["error"]


# ---------------------------------------------------------------------------
# SDK-001: shared HTTP client (no client-per-call)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_client_returns_shared_instance():
    c1 = api_client.get_client()
    c2 = api_client.get_client()
    assert c1 is c2
    await api_client.aclose_client()


@pytest.mark.asyncio
async def test_aclose_client_resets_and_recreates():
    c1 = api_client.get_client()
    await api_client.aclose_client()
    assert api_client._client is None
    c2 = api_client.get_client()
    assert c2 is not c1
    await api_client.aclose_client()


@respx.mock
@pytest.mark.asyncio
async def test_fetch_reuses_shared_client_without_closing(monkeypatch):
    ip = "203.0.113.10"
    monkeypatch.setattr(api_client.net, "_resolve", _pin_resolver(ip))
    url = api_client.build_zhlex_permalink_url("412.100")
    respx.get(api_client.net._pin_url(url, ip)).mock(
        return_value=httpx.Response(200, html="<title>Volksschulgesetz</title>")
    )
    before = api_client.get_client()
    await api_client.fetch_zhlex_metadata("412.100")
    # Same client object survives the call (not closed per request).
    assert api_client._client is before
    assert api_client._client.is_closed is False
    await api_client.aclose_client()
