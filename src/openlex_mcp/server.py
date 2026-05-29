"""
OpenLex MCP Server — Kanton Zürich Rechtssammlung
===================================================
MCP-Server für die Zürcher Gesetzessammlung (ZH-Lex).
Volltextsuche, Artikelextraktion und Bildungsrecht-Tools
basierend auf rcds/swiss_legislation (HuggingFace) und zh.ch.

Datenquellen:
  - HuggingFace rcds/swiss_legislation (Volltext, lokal gecacht)
  - zh.ch ZH-Lex (aktuelle Metadaten, live)

Synergie:
  - swiss-courts-mcp: Gesetze + Rechtsprechung = vollständige Recherche
  - zurich-opendata-mcp: Gesetze + Stadtratsbeschlüsse = Kontext

Transport: stdio (lokal) und streamable-http (Cloud)
"""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal, NoReturn

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from openlex_mcp import api_client
from openlex_mcp.data_cache import LawCache
from openlex_mcp.law_parser import (
    extract_article,
    format_article,
    format_article_list,
    search_in_articles,
)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

MAX_RESULTS_DEFAULT = 20
MAX_RESULTS_LIMIT = 50

# MCP protocol version this server is built and tested against (ARCH-012).
# Update when the SDK is upgraded to a new protocol version.
MCP_PROTOCOL_VERSION = "2025-11-25"

SOURCE_FOOTER = (
    "\n---\n*Quelle: Kanton Zürich Rechtssammlung — "
    "HuggingFace rcds/swiss_legislation (CC-BY-SA 4.0) & zh.ch*"
)

# Bildungsrecht Ordnungsnummern-Prefix
EDUCATION_SR_PREFIX = "412"

# Globaler Cache (wird beim ersten Tool-Aufruf initialisiert)
_cache: LawCache | None = None

# Logger schreibt nach stderr (stdout ist dem JSON-RPC-Stream vorbehalten, OBS-004)
logger = logging.getLogger("openlex_mcp")


# ---------------------------------------------------------------------------
# Settings (ARCH-004 / SCALE-001)
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables (ARCH-004).

    All fields map 1-to-1 to an environment variable of the same name (upper-
    cased by pydantic-settings). CLI flags (--host / --port / --http) are still
    accepted for backward compatibility and override Settings values.
    """

    model_config = SettingsConfigDict(extra="ignore")

    mcp_host: str = "127.0.0.1"
    mcp_port: int = Field(default=8000, ge=1, le=65535)
    # SCALE-001: select transport via env var; "streamable-http" triggers HTTP mode.
    mcp_transport: Literal["stdio", "streamable-http"] = "stdio"
    mcp_cors_origins: str = ""
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.mcp_cors_origins.split(",") if o.strip()]


def _fail(exc: Exception, context: str) -> NoReturn:
    """Loggt den Originalfehler nach stderr und wirft einen maskierten ToolError.

    Erfüllt OBS-001 (Execution-Errors werden als `isError`-Tool-Result
    zurückgegeben, nicht als JSON-RPC-Protocol-Error) und OBS-002 (keine
    Stacktraces / Internals gelangen ans LLM — nur eine handlungsweisende,
    maskierte Meldung; der Originalfehler bleibt ausschliesslich im Server-Log).
    """
    logger.exception("%s fehlgeschlagen", context)
    raise ToolError(api_client.handle_error(exc, context)) from exc


def _get_cache() -> LawCache:
    """Lazy-Initialisierung des Cache."""
    global _cache
    if _cache is None:
        _cache = LawCache()
        _cache.ensure_loaded()
    return _cache


# ---------------------------------------------------------------------------
# Lifespan (SDK-001)
# ---------------------------------------------------------------------------


@dataclass
class AppContext:
    """Lifespan-Kontext für geteilte, server-weite Ressourcen."""

    started: bool = True


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Verwaltet server-weite Ressourcen über den gesamten Lifecycle.

    SDK-001: erstellt beim Start einen einzigen, geteilten httpx-Client
    (kein neuer Client pro Tool-Call) und schliesst ihn beim Shutdown im
    `finally`-Block. Bei einem Multi-Server-Setup würde hier ein
    `AsyncExitStack` mehrere Ressourcen gemeinsam verwalten.
    """
    api_client.get_client()
    logger.info("Lifespan gestartet — geteilter HTTP-Client bereit")
    try:
        yield AppContext()
    finally:
        await api_client.aclose_client()
        logger.info("Lifespan beendet — HTTP-Client geschlossen")


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "openlex_mcp",
    instructions=(
        "MCP-Server für die Zürcher Gesetzessammlung (ZH-Lex / Kanton Zürich). "
        "Volltextsuche in ~970 kantonalen Gesetzen, Artikel-Extraktion, "
        "und spezialisierte Bildungsrecht-Suche (Volksschulgesetz, "
        "Lehrerpersonalverordnung etc.). "
        "Daten: HuggingFace rcds/swiss_legislation (lokal gecacht) + zh.ch (live Metadaten). "
        "Ideal in Kombination mit swiss-courts-mcp (Rechtsprechung) und "
        "zurich-opendata-mcp (Stadtratsbeschlüsse)."
    ),
    lifespan=app_lifespan,
)


# ---------------------------------------------------------------------------
# Input-Modelle
# ---------------------------------------------------------------------------


class SearchLawsInput(BaseModel):
    """Volltextsuche in allen Zürcher Gesetzen."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    query: str = Field(
        ...,
        description=(
            "Suchbegriff(e) für Volltextsuche in Gesetzestexten. "
            "Beispiele: 'Tagesschule', 'Datenschutz', 'Baubewilligung'. "
            "FTS5-Syntax möglich: 'Elternrat OR Elternmitwirkung'."
        ),
        min_length=2,
        max_length=500,
    )
    active_only: bool = Field(
        default=True,
        description="Nur aktuell gültige Gesetze durchsuchen.",
    )
    sr_prefix: str | None = Field(
        default=None,
        description=(
            "Ordnungsnummer-Prefix filtern. Beispiele: "
            "'412' = Bildungsrecht, '131' = Verfassung, "
            "'331' = Steuerrecht. Leer = alle."
        ),
        max_length=20,
    )
    limit: int = Field(
        default=MAX_RESULTS_DEFAULT,
        ge=1,
        le=MAX_RESULTS_LIMIT,
        description="Maximale Trefferzahl.",
    )


class GetLawInput(BaseModel):
    """Gesetz nach Ordnungsnummer oder Abkürzung abrufen."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    identifier: str = Field(
        ...,
        description=(
            "Ordnungsnummer (z.B. '412.100') ODER Abkürzung (z.B. 'VSG'). "
            "Bekannte Abkürzungen: VSG (Volksschulgesetz), VSV (Volksschulverordnung), "
            "LPG (Lehrpersonalgesetz), LPVO (Lehrpersonalverordnung), "
            "PBG (Planungs- und Baugesetz), StG (Steuergesetz)."
        ),
        min_length=1,
        max_length=50,
    )
    include_content: bool = Field(
        default=False,
        description="Volltext einschliessen (kann sehr lang sein). Standard: nur Metadaten.",
    )


class GetArticleInput(BaseModel):
    """Einzelnen Artikel aus einem Gesetz extrahieren."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    law_identifier: str = Field(
        ...,
        description=(
            "Ordnungsnummer (z.B. '412.100') ODER Abkürzung (z.B. 'VSG') "
            "des Gesetzes."
        ),
        min_length=1,
        max_length=50,
    )
    article_number: str = Field(
        ...,
        description=(
            "Artikelnummer, z.B. '28', '28a', '28bis'. "
            "Ohne 'Art.' Prefix — nur die Nummer."
        ),
        min_length=1,
        max_length=20,
    )


class ListLawsInput(BaseModel):
    """Gesetze auflisten mit optionalem Filter."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    active_only: bool = Field(
        default=True,
        description="Nur aktuell gültige Gesetze.",
    )
    sr_prefix: str | None = Field(
        default=None,
        description=(
            "Filter nach Ordnungsnummer-Prefix. "
            "Beispiele: '412' (Bildung), '131' (Verfassung), "
            "'331' (Steuern), '700' (Bau). Leer = alle."
        ),
        max_length=20,
    )
    limit: int = Field(
        default=MAX_RESULTS_DEFAULT,
        ge=1,
        le=MAX_RESULTS_LIMIT,
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Offset für Paginierung.",
    )


class FindEducationLawsInput(BaseModel):
    """Bildungsrecht-Schnellsuche (LS 412.x Serie)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    query: str = Field(
        ...,
        description=(
            "Suchbegriff im Bildungsrecht. Sucht nur in Gesetzen mit "
            "Ordnungsnummer 412.x (Volksschule, Lehrpersonal, Sonderpädagogik etc.). "
            "Beispiele: 'Kindergarten', 'Schulleitungen', 'Tagesstrukturen'."
        ),
        min_length=2,
        max_length=500,
    )
    limit: int = Field(default=MAX_RESULTS_DEFAULT, ge=1, le=MAX_RESULTS_LIMIT)


class SearchArticlesInput(BaseModel):
    """Suche innerhalb der Artikel eines bestimmten Gesetzes."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    law_identifier: str = Field(
        ...,
        description="Ordnungsnummer oder Abkürzung des Gesetzes.",
        min_length=1,
        max_length=50,
    )
    query: str = Field(
        ...,
        description=(
            "Suchbegriff in den Artikeln. "
            "Beispiel: 'Elternrat' in VSG → findet alle Artikel mit 'Elternrat'."
        ),
        min_length=2,
        max_length=200,
    )


class GetLawMetadataInput(BaseModel):
    """Aktuelle Metadaten von zh.ch abrufen."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    sr_number: str = Field(
        ...,
        description="Ordnungsnummer, z.B. '412.100' (Volksschulgesetz).",
        min_length=1,
        max_length=50,
        pattern=r"^\d+[\d.]*$",
    )


class UpdateCacheInput(BaseModel):
    """Cache aktualisieren."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid", strict=True)
    force: bool = Field(
        default=False,
        description="Cache auch wenn aktuell (<24h) erzwingen.",
    )


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _resolve_law(identifier: str) -> dict | None:
    """Löst einen Identifier (Ordnungsnummer oder Abkürzung) zu einem Gesetz auf."""
    cache = _get_cache()

    # Versuche als Ordnungsnummer
    law = cache.get_by_sr_number(identifier)
    if law:
        return law

    # Versuche als Abkürzung
    law = cache.get_by_abbreviation(identifier)
    if law:
        return law

    return None


def _format_law_summary(law: dict, idx: int = 0) -> str:
    """Formatiert ein Gesetz als kompakte Markdown-Zusammenfassung."""
    prefix = f"### {idx}. " if idx > 0 else "### "
    abbr = f" ({law['abbreviation']})" if law.get("abbreviation") else ""
    status = "In Kraft" if law.get("is_active") else "Aufgehoben"

    lines = [
        f"{prefix}{law['title']}{abbr}",
        f"- **Ordnungsnr.:** {law.get('sr_number', '—')}",
        f"- **Status:** {status}",
    ]
    if law.get("short_desc"):
        lines.append(f"- **Kurzbeschreibung:** {law['short_desc']}")
    if law.get("version_since"):
        lines.append(f"- **Version seit:** {law['version_since'][:10]}")

    # Snippet wenn vorhanden (aus FTS5-Suche)
    if law.get("snippet"):
        lines.append(f"- **Fundstelle:** ...{law['snippet']}...")

    return "\n".join(lines)


def _format_law_detail(law: dict, include_content: bool = False) -> str:
    """Formatiert ein Gesetz als detaillierte Markdown-Ansicht."""
    abbr = law.get("abbreviation", "")
    status = "In Kraft" if law.get("is_active") else "Aufgehoben"

    lines = [
        f"## {law['title']}",
        "",
        "| Feld | Wert |",
        "|------|------|",
        f"| **Ordnungsnr.** | {law.get('sr_number', '—')} |",
        f"| **Abkürzung** | {abbr or '—'} |",
        f"| **Status** | {status} |",
    ]
    if law.get("short_desc"):
        lines.append(f"| **Kurzbeschreibung** | {law['short_desc']} |")
    if law.get("version_since"):
        lines.append(f"| **Version seit** | {law['version_since'][:10]} |")
    if law.get("family_since"):
        lines.append(f"| **Erstfassung** | {law['family_since'][:10]} |")
    if law.get("pdf_url"):
        lines.append(f"| **PDF** | [Download]({law['pdf_url']}) |")
    if law.get("html_url"):
        lines.append(f"| **HTML** | [Online]({law['html_url']}) |")

    # ZH-Lex Link
    sr = law.get("sr_number", "")
    if sr:
        zhlex_url = api_client.build_zhlex_search_url(sr)
        lines.append(f"| **ZH-Lex** | [zh.ch]({zhlex_url}) |")

    if include_content:
        content = law.get("pdf_content") or law.get("html_content") or ""
        if content:
            # Erste 5000 Zeichen (mit Hinweis wenn gekürzt)
            if len(content) > 5000:
                content = content[:5000] + "\n\n*[... Text gekürzt — verwende openlex__zhlaw_get_article für einzelne Artikel]*"
            lines.extend(["", "### Volltext", "", content])

    return "\n".join(lines)


def _result_header(count: int, total: int, desc: str) -> str:
    """Standardisierter Ergebnisheader."""
    if total > count:
        return f"## {desc}\n**Treffer:** {count} von {total} angezeigt\n"
    return f"## {desc}\n**Treffer:** {total}\n"


# ---------------------------------------------------------------------------
# Tool 1: Volltextsuche
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_search_laws",
    annotations={
        "title": "Zürcher Gesetze durchsuchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_search_laws(params: SearchLawsInput) -> str:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    Durchsucht Titel, Abkürzungen und Volltexte aller ~970 kantonalen Gesetze.
    Unterstützt FTS5-Syntax: AND, OR, NOT, Phrasensuche "...".
    Ergebnisse nach Relevanz sortiert (BM25-Algorithmus).

    Beispiele: 'Tagesschule', 'Datenschutz Gemeinde', 'Elternrat OR Elternmitwirkung'.
    """
    try:
        cache = _get_cache()
        results = cache.search_fulltext(
            params.query,
            active_only=params.active_only,
            sr_prefix=params.sr_prefix,
            limit=params.limit,
        )

        if not results:
            tips = [
                f"Keine Gesetze gefunden für: **{params.query}**",
                "",
                "Tipps:",
                "- Andere Suchbegriffe oder Synonyme versuchen",
                "- Filter entfernen (active_only, sr_prefix)",
                "- FTS5-Syntax: 'Begriff1 OR Begriff2'",
            ]
            return "\n".join(tips) + SOURCE_FOOTER

        parts = [_result_header(
            len(results), len(results),
            f"Zürcher Gesetze: «{params.query}»",
        )]

        for i, law in enumerate(results, 1):
            parts.append(_format_law_summary(law, i))

        return "\n\n".join(parts) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Volltextsuche")


# ---------------------------------------------------------------------------
# Tool 2: Gesetz nach Ordnungsnummer/Abkürzung
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_get_law",
    annotations={
        "title": "Zürcher Gesetz abrufen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_get_law(params: GetLawInput) -> str:
    """Ruft ein Zürcher Gesetz anhand der Ordnungsnummer oder Abkürzung ab.

    Liefert Metadaten (Titel, Status, Datum, Links) und optional den Volltext.
    Unterstützt sowohl LS-Nummern ('412.100') als auch Abkürzungen ('VSG').

    Wichtige Gesetze: VSG (Volksschulgesetz), LPG (Lehrpersonalgesetz),
    PBG (Planungs-/Baugesetz), StG (Steuergesetz), KV (Kantonsverfassung).
    """
    try:
        law = _resolve_law(params.identifier)

        if not law:
            return (
                f"Gesetz nicht gefunden: **{params.identifier}**\n\n"
                f"Tipps:\n"
                f"- Ordnungsnummer prüfen (z.B. '412.100' statt '412100')\n"
                f"- Abkürzung versuchen (z.B. 'VSG')\n"
                f"- Mit openlex__zhlaw_search_laws nach dem Gesetz suchen"
            ) + SOURCE_FOOTER

        return _format_law_detail(law, include_content=params.include_content) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Gesetzesabruf")


# ---------------------------------------------------------------------------
# Tool 3: Artikel-Extraktion
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_get_article",
    annotations={
        "title": "Gesetzesartikel extrahieren",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_get_article(params: GetArticleInput) -> str:
    """Extrahiert einen einzelnen Artikel aus einem Zürcher Gesetz.

    Parst den Gesetzestext und liefert den spezifischen Artikel mit
    Titel, Absätzen und Volltext. Unterstützt Standard-Artikelnummern
    (28), Buchstaben-Artikel (28a) und Bis-Artikel (28bis).

    Beispiel: law_identifier='VSG', article_number='28' → Art. 28 VSG (Elternmitwirkung).
    """
    try:
        law = _resolve_law(params.law_identifier)

        if not law:
            return (
                f"Gesetz nicht gefunden: **{params.law_identifier}**\n\n"
                f"Bitte Ordnungsnummer oder Abkürzung prüfen."
            ) + SOURCE_FOOTER

        content = law.get("pdf_content") or law.get("html_content") or ""
        if not content:
            return (
                f"Kein Volltext verfügbar für: **{law['title']}** ({law.get('sr_number', '')})\n\n"
                f"Der Gesetzestext ist in der Datenquelle nicht vorhanden."
            ) + SOURCE_FOOTER

        article = extract_article(content, params.article_number)

        if not article:
            return (
                f"Art. {params.article_number} nicht gefunden in: "
                f"**{law['title']}** ({law.get('abbreviation', '')})\n\n"
                f"Tipps:\n"
                f"- Artikelnummer prüfen (nur Nummer, ohne 'Art.')\n"
                f"- Mit openlex__zhlaw_search_articles im Gesetz suchen"
            ) + SOURCE_FOOTER

        law_name = law.get("abbreviation") or law.get("sr_number", "")
        result = format_article(article, law_name)

        # Kontext hinzufügen
        sr = law.get("sr_number", "")
        if sr:
            zhlex_url = api_client.build_zhlex_search_url(sr)
            result += f"\n\n**Gesetz:** [{law['title']}]({zhlex_url})"

        return result + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Artikelextraktion")


# ---------------------------------------------------------------------------
# Tool 4: Gesetze auflisten
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_list_laws",
    annotations={
        "title": "Zürcher Gesetze auflisten",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_list_laws(params: ListLawsInput) -> str:
    """Listet Zürcher Gesetze auf mit optionalem Filter nach Rechtsgebiet.

    Nützliche Ordnungsnummer-Prefixe:
    - 131: Verfassung und Volksrechte
    - 170: Verwaltungsrechtspflege
    - 331: Steuern
    - 412: Volksschule und Bildung
    - 700: Raumplanung und Bau
    - 810: Gesundheit
    """
    try:
        cache = _get_cache()
        laws, total = cache.list_laws(
            active_only=params.active_only,
            sr_prefix=params.sr_prefix,
            limit=params.limit,
            offset=params.offset,
        )

        if not laws:
            return "Keine Gesetze gefunden mit den angegebenen Filtern." + SOURCE_FOOTER

        desc = "Zürcher Gesetze"
        if params.sr_prefix:
            desc += f" (LS {params.sr_prefix}.*)"

        parts = [_result_header(len(laws), total, desc)]

        # Kompakte Tabelle
        parts.append("| Nr. | Ordnungsnr. | Abk. | Titel |")
        parts.append("|-----|-------------|------|-------|")
        for i, law in enumerate(laws, params.offset + 1):
            abbr = law.get("abbreviation", "")
            title = law.get("title", "")
            if len(title) > 60:
                title = title[:57] + "..."
            sr = law.get("sr_number", "")
            parts.append(f"| {i} | {sr} | {abbr} | {title} |")

        if total > params.offset + len(laws):
            parts.append(
                f"\n*Weitere Ergebnisse: offset={params.offset + len(laws)}*"
            )

        return "\n".join(parts) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Gesetzesliste")


# ---------------------------------------------------------------------------
# Tool 5: Bildungsrecht-Schnellsuche
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_find_education_laws",
    annotations={
        "title": "Bildungsrecht suchen (LS 412.x)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_find_education_laws(params: FindEducationLawsInput) -> str:
    """Sucht gezielt im Zürcher Bildungsrecht (Ordnungsnummern 412.x).

    Spezialisierte Suche für das Schul- und Sportdepartement (SSD).
    Durchsucht nur Gesetze der 412er-Serie: Volksschulgesetz (VSG),
    Volksschulverordnung (VSV), Lehrpersonalgesetz (LPG),
    Lehrpersonalverordnung (LPVO), Sonderpädagogik-Verordnung (VSM) etc.

    Synergie: Fundstelle + swiss-courts-mcp → Rechtsprechung dazu finden.
    """
    try:
        cache = _get_cache()
        results = cache.search_fulltext(
            params.query,
            active_only=True,
            sr_prefix=EDUCATION_SR_PREFIX,
            limit=params.limit,
        )

        if not results:
            # Fallback: breitere Suche ohne Prefix
            broader = cache.search_fulltext(params.query, active_only=True, limit=5)
            if broader:
                parts = [
                    f"Keine Treffer im Bildungsrecht (412.x) für: **{params.query}**",
                    "",
                    "Aber in anderen Rechtsgebieten gefunden:",
                    "",
                ]
                for i, law in enumerate(broader, 1):
                    parts.append(_format_law_summary(law, i))
                return "\n".join(parts) + SOURCE_FOOTER

            return (
                f"Keine Gesetze gefunden für: **{params.query}**\n\n"
                f"Tipps:\n"
                f"- Synonyme versuchen (z.B. 'Tagesstruktur' statt 'Tagesschule')\n"
                f"- openlex__zhlaw_search_laws für alle Rechtsgebiete nutzen"
            ) + SOURCE_FOOTER

        parts = [_result_header(
            len(results), len(results),
            f"Bildungsrecht (412.x): «{params.query}»",
        )]

        for i, law in enumerate(results, 1):
            parts.append(_format_law_summary(law, i))

        return "\n\n".join(parts) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Bildungsrecht-Suche")


# ---------------------------------------------------------------------------
# Tool 6: Suche in Artikeln
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_search_articles",
    annotations={
        "title": "In Gesetzesartikeln suchen",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def zhlaw_search_articles(params: SearchArticlesInput) -> str:
    """Durchsucht alle Artikel eines bestimmten Gesetzes nach einem Begriff.

    Parst das Gesetz in einzelne Artikel und findet alle, die den
    Suchbegriff im Titel oder Inhalt enthalten.

    Beispiel: law_identifier='VSG', query='Elternrat'
    → Findet alle VSG-Artikel die 'Elternrat' erwähnen.
    """
    try:
        law = _resolve_law(params.law_identifier)

        if not law:
            return (
                f"Gesetz nicht gefunden: **{params.law_identifier}**"
            ) + SOURCE_FOOTER

        content = law.get("pdf_content") or law.get("html_content") or ""
        if not content:
            return (
                f"Kein Volltext verfügbar für: **{law['title']}**"
            ) + SOURCE_FOOTER

        matching_articles = search_in_articles(content, params.query)

        if not matching_articles:
            return (
                f"Kein Artikel mit '{params.query}' gefunden in: "
                f"**{law['title']}** ({law.get('abbreviation', '')})"
            ) + SOURCE_FOOTER

        law_name = law.get("abbreviation") or law.get("sr_number", "")
        header = (
            f"## Artikel mit «{params.query}» in {law['title']} "
            f"({law_name})\n"
            f"**Treffer:** {len(matching_articles)} Artikel\n"
        )

        return header + "\n" + format_article_list(matching_articles, law_name) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Artikelsuche")


# ---------------------------------------------------------------------------
# Tool 7: Aktuelle Metadaten von zh.ch
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_get_law_metadata",
    annotations={
        "title": "Aktuelle Metadaten von zh.ch",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def zhlaw_get_law_metadata(params: GetLawMetadataInput) -> str:
    """Ruft aktuelle Metadaten eines Gesetzes live von zh.ch ab.

    Liefert den aktuellen Stand direkt von der offiziellen Website:
    Seitentitel, PDF-Links, Änderungsdaten und ZH-Lex URL.
    Nützlich um zu prüfen ob ein Gesetz kürzlich geändert wurde.
    """
    try:
        # Zuerst aus Cache für Kontext
        cache = _get_cache()
        cached_law = cache.get_by_sr_number(params.sr_number)

        # Live-Metadaten von zh.ch
        metadata = await api_client.fetch_zhlex_metadata(params.sr_number)

        lines = [f"## Metadaten: LS {params.sr_number}"]

        if cached_law:
            lines.extend([
                "",
                f"**Gesetz:** {cached_law['title']}",
                f"**Abkürzung:** {cached_law.get('abbreviation', '—')}",
            ])

        lines.append("")

        if metadata.get("found"):
            lines.append("### Live-Daten von zh.ch")
            lines.append("")

            if metadata.get("page_title"):
                lines.append(f"- **Seitentitel:** {metadata['page_title']}")
            if metadata.get("enactment_date"):
                lines.append(f"- **Erlassdatum:** {metadata['enactment_date']}")
            if metadata.get("last_change"):
                lines.append(f"- **Letzte Änderung:** {metadata['last_change']}")

            lines.append(f"- **ZH-Lex URL:** [{metadata['url']}]({metadata['url']})")

            pdf_links = metadata.get("pdf_links", [])
            if pdf_links:
                lines.append("")
                lines.append("### PDF-Downloads")
                for link in pdf_links:
                    lines.append(f"- [PDF]({link})")
        else:
            error = metadata.get("error", metadata.get("message", "Unbekannter Fehler"))
            lines.append(f"**Warnung:** Konnte keine Live-Daten abrufen: {error}")
            if metadata.get("url"):
                lines.append(f"- **Versuchte URL:** {metadata['url']}")

        # LexFind-Link
        lexfind_url = api_client.build_lexfind_url(params.sr_number)
        lines.extend(["", f"**LexFind:** [{lexfind_url}]({lexfind_url})"])

        return "\n".join(lines) + SOURCE_FOOTER

    except Exception as e:
        _fail(e, "Metadaten-Abruf")


# ---------------------------------------------------------------------------
# Tool 8: Cache aktualisieren
# ---------------------------------------------------------------------------


@mcp.tool(
    name="openlex__zhlaw_update_cache",
    annotations={
        "title": "Gesetzes-Cache aktualisieren",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    },
)
async def zhlaw_update_cache(params: UpdateCacheInput) -> str:
    """Aktualisiert den lokalen Cache der Zürcher Gesetzesdaten.

    Lädt die neuesten Daten von HuggingFace (rcds/swiss_legislation)
    und aktualisiert die lokale SQLite-Datenbank mit FTS5-Index.
    Normalerweise nur nötig wenn Daten >24h alt sind.
    """
    try:
        cache = _get_cache()
        result = cache.load_from_huggingface(force=params.force)

        status = result.get("status", "unknown")
        if status == "cache_fresh":
            count = result.get("total", 0)
            return (
                f"## Cache ist aktuell\n\n"
                f"**Gesetze im Cache:** {count}\n"
                f"Der Cache ist weniger als 24 Stunden alt.\n"
                f"Verwende `force=True` um trotzdem zu aktualisieren."
            )
        elif status == "ok":
            return (
                f"## Cache aktualisiert\n\n"
                f"**Geladene Gesetze:** {result['loaded']}\n"
                f"**Dauer:** {result['duration_s']}s\n"
                f"**Quelle:** HuggingFace rcds/swiss_legislation"
            )
        elif status == "error":
            return f"## Fehler beim Cache-Update\n\n{result.get('message', 'Unbekannter Fehler')}"
        else:
            return f"## Cache-Status: {status}\n\n**Gesetze:** {result.get('total', 0)}"

    except Exception as e:
        _fail(e, "Cache-Update")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def _in_container() -> bool:
    """Heuristik: läuft der Prozess in einem Container / Cloud-Runtime?"""
    return bool(
        os.path.exists("/.dockerenv")
        or os.environ.get("KUBERNETES_SERVICE_HOST")
        or os.environ.get("RENDER")
        or os.environ.get("RAILWAY_PROJECT_ID")
    )


def _warn_on_public_binding(host: str) -> None:
    """Warnt, wenn ausserhalb eines Containers an alle Interfaces gebunden wird.

    Ein 0.0.0.0-Binding auf einem Laptop im öffentlichen WLAN macht den
    Server für alle Geräte im Subnetz erreichbar (NeighborJack, SEC-016).
    """
    if host in ("0.0.0.0", "::") and not _in_container():
        logging.warning(
            "Binding to %s outside a container context exposes the MCP "
            "server to the local network (NeighborJack risk). Use "
            "MCP_HOST=127.0.0.1 for local development.",
            host,
        )


def _resolve_http_host_port() -> tuple[str, int]:
    """Ermittelt Host/Port für den HTTP-Transport.

    Reihenfolge: CLI-Argument (--host/--port) > Settings (MCP_HOST/MCP_PORT
    env vars) > sicherer Default (127.0.0.1:8000).
    0.0.0.0 wird niemals als Code-Default gesetzt — Container müssen
    MCP_HOST=0.0.0.0 explizit setzen (siehe README / Dockerfile).
    """
    s = Settings()
    host, port = s.mcp_host, s.mcp_port
    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
    return host, port


def _build_http_app():
    """Baut die Streamable-HTTP-App inklusive CORS (SDK-004).

    `Mcp-Session-Id` wird via `expose_headers` (Browser darf den Header lesen)
    und `allow_headers` (Browser darf ihn bei Folge-Requests senden) freigegeben.
    `allow_origins` ist **kein** Wildcard — Origins werden explizit über die
    Env-Var `MCP_CORS_ORIGINS` (kommagetrennt) gesetzt; Default ist leer.
    """
    from starlette.middleware.cors import CORSMiddleware

    app = mcp.streamable_http_app()
    origins = Settings().cors_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Mcp-Session-Id",
            "Last-Event-ID",
            "MCP-Protocol-Version",
        ],
        expose_headers=["Mcp-Session-Id"],
    )
    return app


def main():
    """Startet den MCP-Server mit Dual-Transport (stdio oder streamable-http).

    Transport-Auswahl (SCALE-001):
      1. MCP_TRANSPORT=streamable-http env var  → HTTP
      2. --http CLI flag                        → HTTP (backward compat.)
      3. Default                                → stdio
    """
    settings = Settings()
    # Logging explizit nach stderr — stdout ist dem JSON-RPC-Stream
    # vorbehalten (OBS-004). level via LOG_LEVEL überschreibbar.
    logging.basicConfig(
        stream=sys.stderr,
        level=settings.log_level.upper(),
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
    )
    use_http = settings.mcp_transport == "streamable-http" or "--http" in sys.argv
    if use_http:
        import uvicorn

        host, port = _resolve_http_host_port()
        _warn_on_public_binding(host)
        uvicorn.run(_build_http_app(), host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
