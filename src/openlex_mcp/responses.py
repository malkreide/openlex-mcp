"""Strukturierte Tool-Response-Envelopes (SDK-002).

Statt vorformatierter Markdown-Strings geben alle Tools ein typisiertes
Pydantic-Envelope zurück: ``source`` (Provenienz-Text), ``provenance``
(Literal-Quelle), ``result_type`` (Literal), ``count`` und eine typisierte
``results``-Liste. ``message`` trägt optionale, menschenlesbare Hinweise
(z. B. „nicht gefunden“-Guidance).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SOURCE = (
    "Kanton Zürich Rechtssammlung — HuggingFace rcds/swiss_legislation "
    "(CC-BY-SA 4.0) & zh.ch"
)

Provenance = Literal["cache", "live", "parser", "cache+parser", "none"]


# ---------------------------------------------------------------------------
# Result-Item-Modelle
# ---------------------------------------------------------------------------


class LawSummary(BaseModel):
    """Kompakte Gesetzes-Zusammenfassung (Such-/Listenergebnis)."""

    sr_number: str | None = None
    title: str
    abbreviation: str | None = None
    is_active: bool
    short_desc: str | None = None
    version_since: str | None = None
    snippet: str | None = None


class LawDetail(LawSummary):
    """Detaillierte Gesetzes-Ansicht (optional mit Volltext)."""

    family_since: str | None = None
    pdf_url: str | None = None
    html_url: str | None = None
    zhlex_url: str | None = None
    content: str | None = None
    content_truncated: bool = False


class ArticleItem(BaseModel):
    """Ein extrahierter Gesetzesartikel."""

    number: str
    title: str | None = None
    content: str
    paragraphs: list[str] = Field(default_factory=list)
    law: str | None = None
    law_title: str | None = None
    zhlex_url: str | None = None


class MetadataItem(BaseModel):
    """Live-Metadaten von zh.ch."""

    sr_number: str
    found: bool
    url: str | None = None
    page_title: str | None = None
    enactment_date: str | None = None
    last_change: str | None = None
    pdf_links: list[str] = Field(default_factory=list)
    lexfind_url: str | None = None
    cached_title: str | None = None
    cached_abbreviation: str | None = None
    error: str | None = None


class CacheStatusItem(BaseModel):
    """Status eines Cache-Update-Vorgangs."""

    status: Literal["ok", "cache_fresh", "error", "already_loaded", "unknown"]
    total: int = 0
    loaded: int = 0
    duration_s: float | None = None
    detail: str | None = None


# ---------------------------------------------------------------------------
# Envelope-Basis + tool-spezifische Responses
# ---------------------------------------------------------------------------


class Envelope(BaseModel):
    """Gemeinsames Response-Envelope (source / provenance / count / message)."""

    source: str = SOURCE
    provenance: Provenance
    count: int = 0
    message: str | None = None


class LawListResponse(Envelope):
    result_type: Literal["law_summaries"] = "law_summaries"
    results: list[LawSummary] = Field(default_factory=list)


class LawDetailResponse(Envelope):
    result_type: Literal["law_detail"] = "law_detail"
    results: list[LawDetail] = Field(default_factory=list)


class ArticleResponse(Envelope):
    result_type: Literal["articles"] = "articles"
    results: list[ArticleItem] = Field(default_factory=list)


class MetadataResponse(Envelope):
    result_type: Literal["metadata"] = "metadata"
    results: list[MetadataItem] = Field(default_factory=list)


class CacheStatusResponse(Envelope):
    result_type: Literal["cache_status"] = "cache_status"
    results: list[CacheStatusItem] = Field(default_factory=list)
