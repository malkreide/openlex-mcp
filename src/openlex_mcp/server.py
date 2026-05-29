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

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from openlex_mcp import api_client
from openlex_mcp.data_cache import LawCache
from openlex_mcp.law_parser import (
    Article,
    extract_article,
    search_in_articles,
)
from openlex_mcp.logging_config import configure_logging, get_logger, tool_logger
from openlex_mcp.responses import (
    ArticleItem,
    ArticleResponse,
    CacheStatusItem,
    CacheStatusResponse,
    LawDetail,
    LawDetailResponse,
    LawListResponse,
    LawSummary,
    MetadataItem,
    MetadataResponse,
)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

MAX_RESULTS_DEFAULT = 20
MAX_RESULTS_LIMIT = 50

# MCP protocol version this server is built and tested against (ARCH-012).
# Update when the SDK is upgraded to a new protocol version.
MCP_PROTOCOL_VERSION = "2025-11-25"

# Bildungsrecht Ordnungsnummern-Prefix
EDUCATION_SR_PREFIX = "412"

# Globaler Cache (wird beim ersten Tool-Aufruf initialisiert)
_cache: LawCache | None = None

# Strukturierter Logger (structlog, JSON nach stderr — OBS-003 / OBS-004).
logger = get_logger("openlex_mcp")


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


def _fail(exc: Exception, context: str, log=None) -> NoReturn:
    """Loggt den Originalfehler strukturiert und wirft einen maskierten ToolError.

    Erfüllt OBS-001 (Execution-Errors werden als `isError`-Tool-Result
    zurückgegeben, nicht als JSON-RPC-Protocol-Error) und OBS-002 (keine
    Stacktraces / Internals gelangen ans LLM — nur eine handlungsweisende,
    maskierte Meldung; der Originalfehler bleibt ausschliesslich im Server-Log).
    Der gebundene Logger (`log`) trägt Tool-Name + Correlation-ID (OBS-003).
    """
    (log or logger).exception("tool_execution_failed", context=context)
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


def _to_summary(law: dict) -> LawSummary:
    """Konvertiert ein Cache-Gesetz in ein LawSummary-Modell (SDK-002)."""
    return LawSummary(
        sr_number=law.get("sr_number") or None,
        title=law["title"],
        abbreviation=law.get("abbreviation") or None,
        is_active=bool(law.get("is_active")),
        short_desc=law.get("short_desc") or None,
        version_since=(law["version_since"][:10] if law.get("version_since") else None),
        snippet=law.get("snippet") or None,
    )


def _to_detail(law: dict, include_content: bool = False) -> LawDetail:
    """Konvertiert ein Cache-Gesetz in ein LawDetail-Modell (SDK-002)."""
    sr = law.get("sr_number") or None
    zhlex_url = api_client.build_zhlex_search_url(sr) if sr else None

    content: str | None = None
    truncated = False
    if include_content:
        raw = law.get("pdf_content") or law.get("html_content") or ""
        if raw:
            if len(raw) > 5000:
                content = raw[:5000]
                truncated = True
            else:
                content = raw

    return LawDetail(
        sr_number=sr,
        title=law["title"],
        abbreviation=law.get("abbreviation") or None,
        is_active=bool(law.get("is_active")),
        short_desc=law.get("short_desc") or None,
        version_since=(law["version_since"][:10] if law.get("version_since") else None),
        family_since=(law["family_since"][:10] if law.get("family_since") else None),
        pdf_url=law.get("pdf_url") or None,
        html_url=law.get("html_url") or None,
        zhlex_url=zhlex_url,
        content=content,
        content_truncated=truncated,
    )


def _to_article_item(
    article: Article, law: dict | None = None
) -> ArticleItem:
    """Konvertiert ein geparstes Article in ein ArticleItem-Modell (SDK-002)."""
    sr = (law or {}).get("sr_number") or None
    return ArticleItem(
        number=article.number,
        title=article.title or None,
        content=article.content,
        paragraphs=list(article.paragraphs),
        law=((law or {}).get("abbreviation") or sr) if law else None,
        law_title=(law or {}).get("title") if law else None,
        zhlex_url=api_client.build_zhlex_search_url(sr) if sr else None,
    )


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
async def zhlaw_search_laws(params: SearchLawsInput) -> LawListResponse:
    """Volltextsuche in allen Zürcher Gesetzen mit FTS5-Ranking.

    <use_case>Allgemeine Suche nach einem Rechtsbegriff über alle ~970 kantonalen
    Gesetze. Wähle dieses Tool wenn das Rechtsgebiet unbekannt ist. Für das
    Bildungsrecht (412.x) ist openlex__zhlaw_find_education_laws schneller und
    präziser. Um Artikel innerhalb eines bekannten Gesetzes zu finden, nutze
    openlex__zhlaw_search_articles.</use_case>

    <important_notes>FTS5-Syntax: AND, OR, NOT, Phrasensuche "...". Ergebnisse
    nach BM25-Relevanz sortiert. Max 50 Treffer pro Aufruf (limit-Parameter).
    sr_prefix filtert nach Rechtsgebiet (412=Bildung, 331=Steuern, 700=Bau).
    Sucht im lokalen Cache — Aktualität der Metadaten via
    openlex__zhlaw_get_law_metadata prüfen.</important_notes>

    <example>query='Elternrat OR Elternmitwirkung', sr_prefix='412', limit=10</example>
    """
    tlog = tool_logger("zhlaw_search_laws")
    try:
        tlog.info("tool_call", query=params.query, limit=params.limit)
        cache = _get_cache()
        results = cache.search_fulltext(
            params.query,
            active_only=params.active_only,
            sr_prefix=params.sr_prefix,
            limit=params.limit,
        )

        if not results:
            return LawListResponse(
                provenance="cache",
                count=0,
                message=(
                    f"Keine Gesetze gefunden für: {params.query}. "
                    "Andere Suchbegriffe/Synonyme versuchen, Filter entfernen "
                    "(active_only, sr_prefix) oder FTS5-Syntax 'Begriff1 OR Begriff2'."
                ),
            )

        summaries = [_to_summary(law) for law in results]
        return LawListResponse(
            provenance="cache",
            count=len(summaries),
            results=summaries,
        )

    except Exception as e:
        _fail(e, "Volltextsuche", tlog)


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
async def zhlaw_get_law(params: GetLawInput) -> LawDetailResponse:
    """Ruft ein Zürcher Gesetz anhand der Ordnungsnummer oder Abkürzung ab.

    <use_case>Wenn die Ordnungsnummer oder Abkürzung eines Gesetzes bereits bekannt
    ist und Metadaten oder Volltext abgerufen werden sollen. Um ein Gesetz erst zu
    finden, openlex__zhlaw_search_laws oder openlex__zhlaw_find_education_laws
    vorschalten.</use_case>

    <important_notes>Unterstützt LS-Nummern ('412.100') und Abkürzungen ('VSG').
    include_content=True liefert den Volltext (bis 5000 Zeichen, dann truncated=True).
    Bei Truncation: openlex__zhlaw_get_article für einzelne Artikel verwenden.
    Wichtige Gesetze: VSG, LPG, PBG, StG, KV.</important_notes>

    <example>identifier='VSG', include_content=False</example>
    """
    tlog = tool_logger("zhlaw_get_law")
    try:
        tlog.info("tool_call", identifier=params.identifier)
        law = _resolve_law(params.identifier)

        if not law:
            return LawDetailResponse(
                provenance="cache",
                count=0,
                message=(
                    f"Gesetz nicht gefunden: {params.identifier}. "
                    "Ordnungsnummer prüfen (z.B. '412.100'), Abkürzung versuchen "
                    "(z.B. 'VSG') oder mit openlex__zhlaw_search_laws suchen."
                ),
            )

        detail = _to_detail(law, include_content=params.include_content)
        message = None
        if detail.content_truncated:
            message = (
                "Volltext auf 5000 Zeichen gekürzt — openlex__zhlaw_get_article "
                "für einzelne Artikel verwenden."
            )
        return LawDetailResponse(
            provenance="cache",
            count=1,
            results=[detail],
            message=message,
        )

    except Exception as e:
        _fail(e, "Gesetzesabruf", tlog)


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
async def zhlaw_get_article(params: GetArticleInput) -> ArticleResponse:
    """Extrahiert einen einzelnen Artikel aus einem Zürcher Gesetz.

    <use_case>Wenn der genaue Wortlaut eines bestimmten Artikels benötigt wird.
    Voraussetzung: Gesetz und Artikelnummer sind bekannt. Um zuerst relevante
    Artikel zu finden: openlex__zhlaw_search_articles nutzen.</use_case>

    <important_notes>Unterstützt Standard-Artikelnummern (28), Buchstaben-Artikel
    (28a) und Bis-Artikel (28bis). Liefert Titel, alle Absätze und Volltext des
    Artikels. Gibt count=0 zurück wenn der Artikel nicht existiert — Artikelnummer
    ohne 'Art.' angeben (nur die Zahl).</important_notes>

    <example>law_identifier='VSG', article_number='28'</example>
    """
    tlog = tool_logger("zhlaw_get_article")
    try:
        tlog.info(
            "tool_call",
            law_identifier=params.law_identifier,
            article_number=params.article_number,
        )
        law = _resolve_law(params.law_identifier)

        if not law:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=(
                    f"Gesetz nicht gefunden: {params.law_identifier}. "
                    "Bitte Ordnungsnummer oder Abkürzung prüfen."
                ),
            )

        content = law.get("pdf_content") or law.get("html_content") or ""
        if not content:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=(
                    f"Kein Volltext verfügbar für: {law['title']} "
                    f"({law.get('sr_number', '')}). "
                    "Der Gesetzestext ist in der Datenquelle nicht vorhanden."
                ),
            )

        article = extract_article(content, params.article_number)

        if not article:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=(
                    f"Art. {params.article_number} nicht gefunden in "
                    f"{law['title']} ({law.get('abbreviation', '')}). "
                    "Artikelnummer prüfen (nur Nummer, ohne 'Art.') oder mit "
                    "openlex__zhlaw_search_articles im Gesetz suchen."
                ),
            )

        return ArticleResponse(
            provenance="cache+parser",
            count=1,
            results=[_to_article_item(article, law)],
        )

    except Exception as e:
        _fail(e, "Artikelextraktion", tlog)


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
async def zhlaw_list_laws(params: ListLawsInput) -> LawListResponse:
    """Listet Zürcher Gesetze auf mit optionalem Filter nach Rechtsgebiet.

    <use_case>Wenn eine strukturierte Übersicht aller Gesetze eines Rechtsgebiets
    benötigt wird (z.B. alle aktiven Bildungsgesetze). Für gezielte Textsuche ist
    openlex__zhlaw_search_laws besser; für reines Bildungsrecht
    openlex__zhlaw_find_education_laws.</use_case>

    <important_notes>sr_prefix filtert nach Ordnungsnummer-Prefix (412=Bildung,
    331=Steuern, 700=Bau, 131=Verfassung, 810=Gesundheit). active_only=True
    blendet aufgehobene Gesetze aus. Unterstützt Paginierung via offset.
    Gibt Titel, Abkürzung, SR-Nummer und Status zurück — keinen Volltext.</important_notes>

    <example>sr_prefix='412', active_only=True, limit=50</example>
    """
    tlog = tool_logger("zhlaw_list_laws")
    try:
        tlog.info("tool_call", sr_prefix=params.sr_prefix, limit=params.limit, offset=params.offset)
        cache = _get_cache()
        laws, total = cache.list_laws(
            active_only=params.active_only,
            sr_prefix=params.sr_prefix,
            limit=params.limit,
            offset=params.offset,
        )

        if not laws:
            return LawListResponse(
                provenance="cache",
                count=0,
                message="Keine Gesetze gefunden mit den angegebenen Filtern.",
            )

        summaries = [_to_summary(law) for law in laws]
        message = None
        if total > params.offset + len(laws):
            message = (
                f"{len(laws)} von {total} angezeigt. "
                f"Weitere Ergebnisse: offset={params.offset + len(laws)}."
            )
        return LawListResponse(
            provenance="cache",
            count=len(summaries),
            results=summaries,
            message=message,
        )

    except Exception as e:
        _fail(e, "Gesetzesliste", tlog)


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
async def zhlaw_find_education_laws(params: FindEducationLawsInput) -> LawListResponse:
    """Sucht gezielt im Zürcher Bildungsrecht (Ordnungsnummern 412.x).

    <use_case>Bevorzuge dieses Tool gegenüber openlex__zhlaw_search_laws wenn die
    Anfrage klar im Bildungsbereich liegt (Schule, Lehrpersonen, Kindergarten,
    Sonderpädagogik, Tagesstrukturen). Schneller und präziser als die allgemeine
    Suche, da nur die 412.x-Serie (VSG, VSV, LPG, LPVO, VSM u.a.) durchsucht
    wird.</use_case>

    <important_notes>Sucht ausschliesslich in aktiven 412.x-Gesetzen. Bei keinen
    Treffern: automatischer Fallback auf alle Rechtsgebiete mit Hinweis im message-
    Feld. Für Artikel innerhalb eines gefundenen Gesetzes:
    openlex__zhlaw_search_articles. Synergie: Fundstelle + swiss-courts-mcp
    → Rechtsprechung finden.</important_notes>

    <example>query='Elternrat', limit=10</example>
    """
    tlog = tool_logger("zhlaw_find_education_laws")
    try:
        tlog.info("tool_call", query=params.query, limit=params.limit)
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
                return LawListResponse(
                    provenance="cache",
                    count=len(broader),
                    results=[_to_summary(law) for law in broader],
                    message=(
                        f"Keine Treffer im Bildungsrecht (412.x) für: {params.query}. "
                        "Stattdessen Treffer in anderen Rechtsgebieten."
                    ),
                )

            return LawListResponse(
                provenance="cache",
                count=0,
                message=(
                    f"Keine Gesetze gefunden für: {params.query}. "
                    "Synonyme versuchen (z.B. 'Tagesstruktur' statt 'Tagesschule') "
                    "oder openlex__zhlaw_search_laws für alle Rechtsgebiete nutzen."
                ),
            )

        return LawListResponse(
            provenance="cache",
            count=len(results),
            results=[_to_summary(law) for law in results],
        )

    except Exception as e:
        _fail(e, "Bildungsrecht-Suche", tlog)


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
async def zhlaw_search_articles(params: SearchArticlesInput) -> ArticleResponse:
    """Durchsucht alle Artikel eines bestimmten Gesetzes nach einem Begriff.

    <use_case>Wenn bekannt ist, in welchem Gesetz gesucht werden soll, aber nicht
    welcher Artikel relevant ist. Liefert alle Treffer-Artikel mit Inhalt.
    Für einen einzelnen Artikel mit bekannter Nummer:
    openlex__zhlaw_get_article.</use_case>

    <important_notes>Parst das Gesetz in einzelne Artikel und durchsucht Titel und
    Inhalt. Suche ist case-insensitive, kein FTS5 (einfaches Substring-Match).
    Gibt count=0 wenn kein Artikel den Begriff enthält. Benötigt Volltext im
    Cache — bei fehlendem Inhalt: Hinweis im message-Feld.</important_notes>

    <example>law_identifier='VSG', query='Elternrat'</example>
    """
    tlog = tool_logger("zhlaw_search_articles")
    try:
        tlog.info("tool_call", law_identifier=params.law_identifier, query=params.query)
        law = _resolve_law(params.law_identifier)

        if not law:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=f"Gesetz nicht gefunden: {params.law_identifier}",
            )

        content = law.get("pdf_content") or law.get("html_content") or ""
        if not content:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=f"Kein Volltext verfügbar für: {law['title']}",
            )

        matching_articles = search_in_articles(content, params.query)

        if not matching_articles:
            return ArticleResponse(
                provenance="cache+parser",
                count=0,
                message=(
                    f"Kein Artikel mit '{params.query}' gefunden in "
                    f"{law['title']} ({law.get('abbreviation', '')})."
                ),
            )

        return ArticleResponse(
            provenance="cache+parser",
            count=len(matching_articles),
            results=[_to_article_item(a, law) for a in matching_articles],
        )

    except Exception as e:
        _fail(e, "Artikelsuche", tlog)


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
async def zhlaw_get_law_metadata(params: GetLawMetadataInput) -> MetadataResponse:
    """Ruft aktuelle Metadaten eines Gesetzes live von zh.ch ab.

    <use_case>Wenn der aktuelle Stand eines Gesetzes auf zh.ch geprüft werden
    soll — z.B. ob es kürzlich geändert wurde, welche PDF-Version aktuell gilt
    oder welche ZH-Lex URL direkt verlinkt werden kann. Einziges Tool mit
    Live-HTTP-Aufruf; alle anderen Tools lesen den lokalen Cache.</use_case>

    <important_notes>Macht einen echten HTTP-Request an www.zh.ch (ca. 1–3 s).
    Erfordert Netzwerkzugang. Liefert: Seitentitel, PDF-Links, Änderungsdatum,
    ZH-Lex URL. Bei 404 oder Timeout: found=False mit Fehlerdetail im error-Feld.
    Nur Ordnungsnummern akzeptiert (kein Abkürzungs-Lookup).</important_notes>

    <example>sr_number='412.100'</example>
    """
    tlog = tool_logger("zhlaw_get_law_metadata")
    try:
        tlog.info("tool_call", sr_number=params.sr_number)
        # Zuerst aus Cache für Kontext
        cache = _get_cache()
        cached_law = cache.get_by_sr_number(params.sr_number)

        # Live-Metadaten von zh.ch
        metadata = await api_client.fetch_zhlex_metadata(params.sr_number)
        lexfind_url = api_client.build_lexfind_url(params.sr_number)

        found = bool(metadata.get("found"))
        error = None if found else metadata.get("error") or metadata.get("message")
        if not found:
            tlog.warning("metadata_unavailable", sr_number=params.sr_number, error=error)

        item = MetadataItem(
            sr_number=params.sr_number,
            found=found,
            url=metadata.get("url"),
            page_title=metadata.get("page_title"),
            enactment_date=metadata.get("enactment_date"),
            last_change=metadata.get("last_change"),
            pdf_links=list(metadata.get("pdf_links", [])),
            lexfind_url=lexfind_url,
            cached_title=cached_law.get("title") if cached_law else None,
            cached_abbreviation=cached_law.get("abbreviation") if cached_law else None,
            error=error,
        )

        return MetadataResponse(
            provenance="live",
            count=1,
            results=[item],
            message=None if found else f"Keine Live-Daten von zh.ch: {error}",
        )

    except Exception as e:
        _fail(e, "Metadaten-Abruf", tlog)


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
async def zhlaw_update_cache(ctx: Context, params: UpdateCacheInput) -> CacheStatusResponse:
    """Aktualisiert den lokalen Cache der Zürcher Gesetzesdaten.

    <use_case>Nur aufrufen wenn Gesetzes-Suchergebnisse veraltet wirken oder
    der Cache explizit neu geladen werden soll. Der Cache wird automatisch beim
    Start befüllt und ist 24 Stunden gültig — manuelles Update ist selten
    nötig.</use_case>

    <important_notes>Lädt ~970 Gesetze von HuggingFace (rcds/swiss_legislation)
    in die lokale SQLite-DB mit FTS5-Index (~25 s erster Lauf). force=False
    überspringt den Download wenn Cache <24h alt (gibt status='cache_fresh'
    zurück). force=True erzwingt Neudownload. Erfordert Internetzugang zu
    HuggingFace.</important_notes>

    <example>force=False</example>
    """
    tlog = tool_logger("zhlaw_update_cache")
    try:
        tlog.info("tool_call", force=params.force)
        await ctx.info("Cache-Update gestartet — prüfe Aktualität…")
        cache = _get_cache()
        await ctx.report_progress(progress=0, total=1)
        result = cache.load_from_huggingface(force=params.force)
        await ctx.report_progress(progress=1, total=1)

        status = result.get("status", "unknown")
        if status not in ("ok", "cache_fresh", "error", "already_loaded"):
            status = "unknown"

        if status == "cache_fresh":
            count = result.get("total", 0)
            await ctx.info(f"Cache ist aktuell — {count} Gesetze im Cache.")
            item = CacheStatusItem(
                status="cache_fresh",
                total=count,
                detail="Cache <24h alt. force=True erzwingt Aktualisierung.",
            )
        elif status == "ok":
            loaded = result["loaded"]
            duration = result["duration_s"]
            await ctx.info(f"Cache-Update abgeschlossen: {loaded} Gesetze in {duration}s geladen.")
            item = CacheStatusItem(
                status="ok",
                loaded=loaded,
                total=result.get("total", loaded),
                duration_s=duration,
                detail="Quelle: HuggingFace rcds/swiss_legislation",
            )
        elif status == "error":
            msg = result.get("message", "Unbekannter Fehler")
            await ctx.warning(f"Cache-Update fehlgeschlagen: {msg}")
            tlog.warning("cache_update_error", detail=msg)
            item = CacheStatusItem(status="error", detail=msg)
        else:
            item = CacheStatusItem(status="unknown", total=result.get("total", 0))

        return CacheStatusResponse(
            provenance="cache",
            count=1,
            results=[item],
            message=item.detail,
        )

    except Exception as e:
        _fail(e, "Cache-Update", tlog)


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
    # Strukturiertes JSON-Logging nach stderr — stdout ist dem JSON-RPC-Stream
    # vorbehalten (OBS-003 / OBS-004). Level via LOG_LEVEL überschreibbar.
    configure_logging(settings.log_level)
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
