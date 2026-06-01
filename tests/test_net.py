"""Unit-Tests für die Outbound-Härtung (SEC-004 / SEC-021 / SEC-005)."""
from __future__ import annotations

import httpx
import pytest
import respx

from openlex_mcp import net


def _fake_resolve(ip: str):
    async def _resolve(_host: str, _port: int) -> list[str]:
        return [ip]

    return _resolve


# ---------------------------------------------------------------------------
# SEC-004: IP blocklist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ip",
    ["169.254.169.254", "10.0.0.5", "127.0.0.1", "192.168.1.1", "172.16.0.1", "::1"],
)
def test_blocked_ips(ip):
    assert net._is_blocked_ip(ip) is True


@pytest.mark.parametrize("ip", ["8.8.8.8", "203.0.113.10", "1.1.1.1"])
def test_public_ips_not_blocked(ip):
    assert net._is_blocked_ip(ip) is False


# ---------------------------------------------------------------------------
# SEC-021: host allow-list
# ---------------------------------------------------------------------------


def test_assert_host_allowed_passes_for_listed():
    net.assert_host_allowed("www.zh.ch")  # must not raise


def test_assert_host_allowed_rejects_unlisted():
    with pytest.raises(net.EgressError):
        net.assert_host_allowed("evil.example.com")


# ---------------------------------------------------------------------------
# SEC-004: scheme + URL gate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_assert_url_allowed_rejects_non_https():
    # www.zh.ch ist NICHT in HTTP_ALLOWED_HOSTS → HTTP bleibt verboten.
    with pytest.raises(net.EgressError):
        await net.assert_url_allowed("http://www.zh.ch/x")


def test_assert_host_allowed_passes_for_legacy_permalink_host():
    net.assert_host_allowed("www.zhlex.zh.ch")  # must not raise


@pytest.mark.asyncio
async def test_assert_url_allowed_accepts_http_for_legacy_host(monkeypatch):
    # www.zhlex.zh.ch liefert nur über HTTP aus → ausnahmsweise erlaubt.
    monkeypatch.setattr(net, "_resolve", _fake_resolve("203.0.113.10"))
    ips = await net.assert_url_allowed(
        "http://www.zhlex.zh.ch/Erlass.html?Open&Ordnr=412.100"
    )
    assert ips == ["203.0.113.10"]


@pytest.mark.asyncio
async def test_assert_url_allowed_rejects_http_for_non_legacy_host():
    # Ein unbekannter Host darf auch dann kein HTTP, wenn er gelistet wäre.
    with pytest.raises(net.EgressError):
        await net.assert_url_allowed("http://evil.example.com/x")


@pytest.mark.asyncio
async def test_assert_url_allowed_rejects_unlisted_host():
    with pytest.raises(net.EgressError):
        await net.assert_url_allowed("https://evil.example.com/x")


@pytest.mark.asyncio
async def test_assert_url_allowed_blocks_metadata_ip(monkeypatch):
    monkeypatch.setattr(net, "_resolve", _fake_resolve("169.254.169.254"))
    with pytest.raises(net.EgressError):
        await net.assert_url_allowed("https://www.zh.ch/x")


@pytest.mark.asyncio
async def test_assert_url_allowed_accepts_public_ip(monkeypatch):
    monkeypatch.setattr(net, "_resolve", _fake_resolve("203.0.113.10"))
    assert await net.assert_url_allowed("https://www.zh.ch/x") == ["203.0.113.10"]


# ---------------------------------------------------------------------------
# SEC-005: DNS pinning
# ---------------------------------------------------------------------------


def test_pin_url_ipv4():
    assert net._pin_url("https://www.zh.ch/a/b.html", "203.0.113.10") == (
        "https://203.0.113.10/a/b.html"
    )


def test_pin_url_ipv6_brackets():
    assert net._pin_url("https://www.zh.ch/a", "2001:db8::1") == "https://[2001:db8::1]/a"


@respx.mock
@pytest.mark.asyncio
async def test_safe_get_pins_ip_and_preserves_host_and_sni(monkeypatch):
    ip = "203.0.113.10"
    monkeypatch.setattr(net, "_resolve", _fake_resolve(ip))
    url = "https://www.zh.ch/page.html"
    route = respx.get(net._pin_url(url, ip)).mock(
        return_value=httpx.Response(200, text="ok")
    )
    async with httpx.AsyncClient() as client:
        resp, final = await net.safe_get(client, url)
    assert resp.status_code == 200
    assert final == url
    req = route.calls.last.request
    assert req.headers["host"] == "www.zh.ch"  # Host preserved despite IP target
    assert req.extensions.get("sni_hostname") == "www.zh.ch"  # TLS SNI preserved


@respx.mock
@pytest.mark.asyncio
async def test_safe_get_blocks_redirect_to_unlisted_host(monkeypatch):
    ip = "203.0.113.10"
    monkeypatch.setattr(net, "_resolve", _fake_resolve(ip))
    url = "https://www.zh.ch/start"
    respx.get(net._pin_url(url, ip)).mock(
        return_value=httpx.Response(302, headers={"location": "https://evil.example.com/x"})
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(net.EgressError):
            await net.safe_get(client, url)
