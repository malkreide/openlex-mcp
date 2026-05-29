"""Strukturiertes Logging mit structlog (OBS-003).

JSON-Ausgabe nach **stderr** (stdout bleibt dem JSON-RPC-Stream vorbehalten,
OBS-004), RFC-5424-kompatible Severity-Stufen (debug/info/warning/error/
critical) und pro-Tool-Call gebundener Kontext (Tool-Name + Correlation-ID).
"""
from __future__ import annotations

import logging
import sys
import uuid

import structlog

_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Konfiguriert structlog mit JSON-Renderer nach stderr.

    Idempotent — mehrfaches Aufrufen (z. B. Tests + main()) ist unschädlich,
    aktualisiert aber das Log-Level.
    """
    global _configured

    logging.basicConfig(
        stream=sys.stderr,
        level=level.upper(),
        format="%(message)s",
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(level.upper())
            if isinstance(logging.getLevelName(level.upper()), int)
            else logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        # Caching is disabled so structlog.testing.capture_logs() works in tests
        # and so a re-configured log level takes effect immediately.
        cache_logger_on_first_use=False,
    )
    _configured = True


def get_logger(name: str = "openlex_mcp"):
    """Liefert einen structlog-Logger (konfiguriert bei Bedarf mit Defaults)."""
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)


def tool_logger(tool: str):
    """Bindet pro Tool-Call Tool-Name + frische Correlation-ID (OBS-003)."""
    return get_logger().bind(tool=tool, correlation_id=uuid.uuid4().hex[:12])
