"""Eingehende Host/Origin-Prüfung des HTTP-Transports (SEC-005, eingehend).

Der Auslöser war kein fehlender Schutz, sondern ein zu strenger: mcp 2.x
aktiviert bei loopback-artigem ``host`` automatisch eine Allow-List auf
``127.0.0.1:*``, und ``streamable_http_app()`` defaultet ohne ``host``-Argument
genau darauf. Der Server band laut Dockerfile ``MCP_HOST=0.0.0.0`` und wies
damit **jede** Anfrage unter einem echten Hostnamen mit HTTP 421 ab —
nachgemessen an der echten ASGI-App, bevor dieser Commit entstand:

    Host 127.0.0.1:8000        -> 200
    Host mcp.example.ch        -> 421
    Host openlex.example.com   -> 421

Diese Tests halten beide Hälften fest: dass ein echter Bind wieder erreichbar
ist, und dass die Allow-List, wenn sie gesetzt wird, portgenau greift.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from openlex_mcp.server import Settings, _build_http_app, build_transport_security

_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def test_loopback_bind_is_protected(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    sec = build_transport_security("127.0.0.1", 8000)
    assert sec is not None
    assert sec.enable_dns_rebinding_protection is True
    assert "127.0.0.1:8000" in sec.allowed_hosts


def test_wildcard_bind_without_allowlist_stays_off(monkeypatch):
    """Der eigentliche Fix.

    Auf ``0.0.0.0`` ist der erreichbare Name hier unbekannt. Eine geratene
    Liste — und der SDK-Loopback-Default ist genau das — reproduziert das
    421-Problem. Also bleibt der Schutz aus und der Aufrufer warnt.
    """
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    assert build_transport_security("0.0.0.0", 8000) is None


def test_wildcard_bind_with_allowlist_is_protected(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "openlex.example.com")
    sec = build_transport_security("0.0.0.0", 8000)
    assert sec is not None
    assert "openlex.example.com" in sec.allowed_hosts
    # Loopback bleibt drin, sonst brechen Container-Health-Checks.
    assert "127.0.0.1:8000" in sec.allowed_hosts


def test_cors_origins_pass_the_transport_check(monkeypatch):
    """Sonst weist der Server genau die Browser-Clients ab, die CORS erlaubt."""
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    monkeypatch.setenv("MCP_CORS_ORIGINS", "https://claude.ai")
    sec = build_transport_security("127.0.0.1", 8000)
    assert "https://claude.ai" in sec.allowed_origins


def test_wildcard_cors_is_not_copied(monkeypatch):
    """``*`` ist als Origin nicht ausdrückbar — literal verglichen wäre es ein
    Host namens ``*``, was nichts erlaubt und alles verwirrt."""
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    monkeypatch.setenv("MCP_CORS_ORIGINS", "*")
    sec = build_transport_security("127.0.0.1", 8000)
    assert "*" not in sec.allowed_origins


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_all_loopback_forms_count_as_local(host, monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    assert build_transport_security(host, 8000) is not None


def _post(app, host_header: str) -> int:
    with TestClient(app) as client:
        return client.post(
            "/mcp", headers={"Host": host_header, **_HEADERS}, json=_INIT
        ).status_code


def test_a_public_bind_is_reachable_again(monkeypatch):
    """Die Regression selbst, durch den echten ASGI-Stack.

    Ohne den ``host``-Kwarg wäre das ein 421 — das ist der Zustand, den dieser
    Commit behebt.
    """
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "")
    assert _post(_build_http_app("0.0.0.0", 8000), "openlex.example.com") == 200


def test_configured_host_is_served(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "openlex.example.com")
    assert _post(_build_http_app("0.0.0.0", 8000), "openlex.example.com") == 200


def test_foreign_host_is_rejected(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "openlex.example.com")
    assert _post(_build_http_app("0.0.0.0", 8000), "evil.example.com") == 421


def test_right_host_wrong_port_is_rejected(monkeypatch):
    """Der tragende Fall.

    ``evil.example.com`` allein beweist wenig: fiele der Schutz auf den
    SDK-Loopback-Default zurück, wäre der ebenfalls abgewiesen. Nur „richtiger
    Hostname, falscher Port" unterscheidet eine portgenaue Allow-List von einer,
    die alles durchlässt — und dieser Test schlägt fehl, sobald
    ``transport_security`` nicht mehr übergeben wird.
    """
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "openlex.example.com:8000")
    assert _post(_build_http_app("0.0.0.0", 8000), "openlex.example.com:9999") == 421


def test_allowed_hosts_setting_is_read_from_the_environment(monkeypatch):
    monkeypatch.setenv("MCP_ALLOWED_HOSTS", "a.example.com, b.example.com")
    assert Settings().allowed_hosts_list == ["a.example.com", "b.example.com"]
