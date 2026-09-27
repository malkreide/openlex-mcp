"""Der Server spricht Spec `2026-07-28` nativ — gemessen am Draht, nicht am Code.

Jede Zusicherung hier laeuft ueber eine echte `Client`-Verbindung, die per
`server/discover` die moderne Aera aushandelt. Ein Blick in Konstanten oder
Konstruktor-Argumente waere auch dann gruen, wenn das SDK sie verwuerfe.

Drei Luecken waren gemessen, bevor es diese Datei gab:

- `serverInfo.version` war `""`. Das SDK setzt bewusst keine eigene Version ein,
  und `MCPServer(...)` bekam keine.
- `openlex__zhlaw_update_cache` meldete sich ueber `ctx.info`/`ctx.warning` —
  die Logging-Faehigkeit ist mit dieser Spec abgekuendigt (SEP-2577). Jeder
  Aufruf warf eine `MCPDeprecationWarning`, auf einer modernen Verbindung kam
  die Meldung ohne Bestellung per `_meta` gar nicht an.
- `server/discover` kuendigt `prompts` und `resources` an, obwohl der Server
  keine registriert: `MCPServer` bedient die Listen immer. Sie trugen deshalb
  «sofort veraltet» und wurden bei jeder Verbindung neu abgefragt.
"""

from __future__ import annotations

import ast
import inspect
import warnings

from mcp import Client
from mcp.shared.exceptions import MCPDeprecationWarning

from openlex_mcp import __version__
from openlex_mcp import server as srv
from openlex_mcp.server import LIST_CACHE_TTL_MS, MCP_PROTOCOL_VERSION, mcp


async def test_die_verbindung_ist_modern() -> None:
    """Voraussetzung aller Tests unten: `Client(mcp)` handelt die moderne Aera
    aus. Faellt sie auf den Handshake zurueck, pruefen die anderen die falsche
    Verbindung."""
    async with Client(mcp) as client:
        assert client.protocol_version == MCP_PROTOCOL_VERSION


async def test_discover_nennt_die_paketversion() -> None:
    async with Client(mcp) as client:
        info = client.server_info

    assert info is not None
    assert info.name == "openlex_mcp"
    assert info.version == __version__
    assert info.version, "serverInfo.version ist leer"


async def test_discover_kuendigt_keine_abgekuendigte_faehigkeit_an() -> None:
    """SEP-2577: `logging` ist abgekuendigt. Registriert der Server einmal einen
    `logging/setLevel`-Handler, kuendigt das SDK die Faehigkeit wieder an."""
    async with Client(mcp) as client:
        caps = client.server_capabilities

    assert caps.logging is None
    assert caps.tools is not None


async def test_die_angekuendigten_listen_tragen_einen_frischehinweis() -> None:
    """Erst die Praemisse, dann die Zusicherung: Die Hinweise auf `prompts/list`
    und `resources/list` stehen nur deshalb in `CACHE_HINTS`, weil `discover`
    diese Flaechen ankuendigt. Verschwindet die Ankuendigung, soll dieser Test
    fallen und die Hinweise zur Diskussion stellen — nicht still weiterlaufen."""
    async with Client(mcp) as client:
        caps = client.server_capabilities
        assert caps.prompts is not None and caps.resources is not None, (
            "discover kuendigt prompts/resources nicht mehr an — dann gehoeren "
            "die Hinweise darauf aus CACHE_HINTS gestrichen"
        )
        ergebnisse = {
            "prompts/list": await client.list_prompts(),
            "resources/list": await client.list_resources(),
            "resources/templates/list": await client.list_resource_templates(),
        }

    for methode, result in ergebnisse.items():
        assert result.ttl_ms == LIST_CACHE_TTL_MS, f"{methode}: ttlMs={result.ttl_ms}"
        assert result.cache_scope == "public", f"{methode}: cacheScope={result.cache_scope}"


async def test_update_cache_ruft_keine_abgekuendigte_api(monkeypatch) -> None:
    """Der einzige Tool-Aufruf mit `Context`, ueber den Draht und mit der
    Abkuendigungswarnung als Fehler. Vor der Umstellung warf jeder Aufruf
    zwei `MCPDeprecationWarning`s."""

    class _Cache:
        def load_from_huggingface(self, force: bool = False) -> dict:
            return {"status": "cache_fresh", "total": 3}

    monkeypatch.setattr(srv, "_get_cache", lambda: _Cache())

    with warnings.catch_warnings():
        warnings.simplefilter("error", MCPDeprecationWarning)
        async with Client(mcp) as client:
            result = await client.call_tool(
                "openlex__zhlaw_update_cache", {"params": {"force": False}}
            )

    assert not result.is_error, result.content
    assert result.structured_content["results"][0]["status"] == "cache_fresh"


# Methoden auf `Context`, die das SDK mit Spec 2026-07-28 abkuendigt (SEP-2577).
_ABGEKUENDIGT = {"log", "debug", "info", "warning", "error"}


def _abgekuendigte_aufrufe(quelle: str) -> list[str]:
    funde = []
    for node in ast.walk(ast.parse(quelle)):
        if not isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        ctx_namen = {
            a.arg
            for a in node.args.args + node.args.kwonlyargs
            if isinstance(a.annotation, ast.Name | ast.Constant)
            and "Context" in ast.unparse(a.annotation)
        }
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Attribute)
                and isinstance(inner.value, ast.Name)
                and inner.value.id in ctx_namen
                and inner.attr in _ABGEKUENDIGT
            ):
                funde.append(f"{node.name}: {inner.value.id}.{inner.attr}")
    return funde


def test_kein_werkzeug_ruft_abgekuendigtes_logging() -> None:
    """Der Laufzeittest oben deckt nur das eine Werkzeug ab, das heute einen
    `Context` nimmt. Diese Pruefung faengt das naechste, bevor es jemand ueber
    den Draht aufruft."""
    funde = _abgekuendigte_aufrufe(inspect.getsource(srv))
    assert not funde, f"abgekuendigte Logging-Aufrufe (SEP-2577): {funde}"


def test_die_pruefung_findet_einen_abgekuendigten_aufruf() -> None:
    """Gegenprobe: dieselbe Pruefung auf einem Schnipsel mit dem alten Muster."""
    schnipsel = (
        "async def tool(ctx: Context, params):\n"
        "    await ctx.info('x')\n"
        "    await ctx.report_progress(progress=0, total=1)\n"
    )
    assert _abgekuendigte_aufrufe(schnipsel) == ["tool: ctx.info"]
