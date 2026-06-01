"""Outbound-Request-Härtung
===========================
Verteidigung gegen SSRF, DNS-Rebinding und unkontrollierten Egress für alle
ausgehenden HTTP-Requests des Servers.

Drei Schutzschichten (Code-Layer):
  - **HTTPS-Enforcement** — `https://` ist die Regel; `http://` nur für explizit
    gelistete Legacy-Hosts (`HTTP_ALLOWED_HOSTS`), siehe SEC-004.
  - **Egress-Allow-List** — nur explizit gelistete Hosts (SEC-021).
  - **SSRF-IP-Block + DNS-Pinning** — der Host wird **einmal** aufgelöst, jede
    resultierende IP gegen private/loopback/link-local/Metadata-Ranges geprüft,
    und die Verbindung an die geprüfte IP gepinnt (Host-Header + TLS-SNI bleiben
    der Originalname) — verhindert TOCTOU/DNS-Rebinding (SEC-004 / SEC-005).

Redirects werden manuell verfolgt, wobei **jedes** Ziel die volle Prüfkette
erneut durchläuft (verhindert Redirect-basiertes SSRF).

Die Network-Layer-Ergänzung (NetworkPolicy / Security Group) ist in
`docs/network-egress.md` dokumentiert.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urlparse, urlunparse

import httpx

# Code-Layer-Egress-Allow-List — bewusst ein FrozenSet, nicht zur Laufzeit
# mutierbar. Erweiterungen siehe docs/network-egress.md.
#   - www.zh.ch       : aktuelle Gesetzessammlung (HTTPS).
#   - www.zhlex.zh.ch : stabile Ordnungsnummer-Permalinks (Erlass.html?Ordnr=…).
#     Dieser Legacy-Dienst liefert nur über HTTP aus (siehe HTTP_ALLOWED_HOSTS).
EGRESS_ALLOWLIST: frozenset[str] = frozenset({"www.zh.ch", "www.zhlex.zh.ch"})

# Hosts, für die ausnahmsweise HTTP (statt HTTPS) erlaubt ist. Die übrigen
# Schutzschichten (Allow-List, IP-Block, DNS-Pinning, Redirect-Gate) gelten
# unverändert. www.zhlex.zh.ch stellt die stabilen Ordnungsnummer-Permalinks
# nur unverschlüsselt bereit; Redirects auf https://www.zh.ch durchlaufen die
# Prüfkette erneut und bleiben damit abgesichert.
HTTP_ALLOWED_HOSTS: frozenset[str] = frozenset({"www.zhlex.zh.ch"})

# Nicht-routbare / interne Bereiche, inkl. Cloud-Metadata 169.254.169.254.
BLOCKED_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = tuple(
    ipaddress.ip_network(n)
    for n in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
    )
)

MAX_REDIRECTS = 5


class EgressError(ValueError):
    """Ausgehender Request wurde durch eine Schutzschicht blockiert."""


def _is_blocked_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return any(ip in net for net in BLOCKED_NETWORKS)


def assert_host_allowed(host: str) -> None:
    """Wirft EgressError, wenn der Host nicht in der Allow-List steht (SEC-021)."""
    if host not in EGRESS_ALLOWLIST:
        raise EgressError(
            f"Host '{host}' nicht in der Egress-Allow-List "
            f"({sorted(EGRESS_ALLOWLIST)})."
        )


async def _resolve(host: str, port: int) -> list[str]:
    """Löst einen Host **einmal** zu seinen IP-Adressen auf (in Reihenfolge)."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips: list[str] = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips


async def assert_url_allowed(url: str) -> list[str]:
    """Prüft Schema + Host-Allow-List + resolved-IPs. Gibt die IPs zurück.

    Erfüllt SEC-004 (HTTPS + IP-Blocklist) und SEC-021 (Host-Allow-List).
    """
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        raise EgressError(f"URL ohne Host: {url!r}.")
    # HTTPS ist die Regel; HTTP nur für explizit gelistete Legacy-Hosts.
    if parsed.scheme == "https":
        pass
    elif parsed.scheme == "http" and host in HTTP_ALLOWED_HOSTS:
        pass
    else:
        raise EgressError(
            f"Schema {parsed.scheme!r} für Host {host!r} nicht erlaubt "
            "(HTTPS erforderlich)."
        )
    assert_host_allowed(host)
    default_port = 80 if parsed.scheme == "http" else 443
    ips = await _resolve(host, parsed.port or default_port)
    if not ips:
        raise EgressError(f"Keine DNS-Auflösung für '{host}'.")
    for ip in ips:
        if _is_blocked_ip(ip):
            raise EgressError(
                f"Blockierte IP {ip} für '{host}' "
                f"(privater/loopback/link-local/Metadata-Bereich)."
            )
    return ips


def _pin_url(url: str, ip: str) -> str:
    """Ersetzt den Host der URL durch die aufgelöste IP (DNS-Pinning, SEC-005)."""
    parsed = urlparse(url)
    host = f"[{ip}]" if ":" in ip else ip
    netloc = f"{host}:{parsed.port}" if parsed.port else host
    return urlunparse(parsed._replace(netloc=netloc))


async def safe_get(
    client: httpx.AsyncClient, url: str, *, max_redirects: int = MAX_REDIRECTS
) -> tuple[httpx.Response, str]:
    """Sicherer GET: HTTPS + Allow-List + IP-Block + DNS-Pinning + Redirect-Gate.

    Returns:
        (response, final_url) — `final_url` ist die logische (host-basierte) URL,
        an der die Antwort gelesen wurde (nach evtl. Redirects).
    """
    current = url
    for _ in range(max_redirects + 1):
        ips = await assert_url_allowed(current)
        host = urlparse(current).hostname or ""
        # An die geprüfte IP pinnen; Host-Header + TLS-SNI bleiben der Name,
        # so dass kein zweiter DNS-Lookup beim Connect stattfindet (kein TOCTOU)
        # und das Zertifikat weiterhin gegen den Hostnamen validiert wird.
        pinned = _pin_url(current, ips[0])
        resp = await client.get(
            pinned,
            headers={"Host": host},
            extensions={"sni_hostname": host},
        )
        if resp.is_redirect and resp.headers.get("location"):
            current = str(httpx.URL(current).join(resp.headers["location"]))
            continue
        return resp, current
    raise EgressError(f"Zu viele Redirects (> {max_redirects}).")
