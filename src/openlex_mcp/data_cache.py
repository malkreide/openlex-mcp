"""
SQLite-Cache für Zürcher Gesetzestexte
=======================================
Lädt Gesetzesdaten von HuggingFace (rcds/swiss_legislation)
und speichert sie in einer lokalen SQLite-Datenbank mit FTS5-Volltextindex.

Architektur:
  - Tabelle `laws`: Metadaten + Volltext aller ZH-Gesetze
  - Tabelle `laws_fts`: FTS5-Index für blitzschnelle Volltextsuche
  - Tabelle `cache_meta`: Zeitstempel des letzten Updates

Datenquelle: HuggingFace rcds/swiss_legislation (CC-BY-SA 4.0)
Filter: canton == "zh", language == "de"
"""

from __future__ import annotations

import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------

HF_DATASET = "rcds/swiss_legislation"
HF_SPLIT = "train"
DB_FILENAME = "zhlex_cache.db"

# Standard-Pfad: neben dem Paket im data/-Ordner
DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CREATE_LAWS_TABLE = """
CREATE TABLE IF NOT EXISTS laws (
    uuid            TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    short_desc      TEXT DEFAULT '',
    abbreviation    TEXT DEFAULT '',
    sr_number       TEXT DEFAULT '',
    is_active       INTEGER DEFAULT 1,
    pdf_url         TEXT DEFAULT '',
    html_url        TEXT DEFAULT '',
    pdf_content     TEXT DEFAULT '',
    html_content    TEXT DEFAULT '',
    version_since   TEXT DEFAULT '',
    family_since    TEXT DEFAULT '',
    canton          TEXT DEFAULT 'zh',
    language        TEXT DEFAULT 'de'
);
"""

_CREATE_FTS_TABLE = """
CREATE VIRTUAL TABLE IF NOT EXISTS laws_fts USING fts5(
    uuid UNINDEXED,
    title,
    short_desc,
    abbreviation,
    sr_number UNINDEXED,
    body,
    tokenize='unicode61 remove_diacritics 2'
);
"""

# Keine Trigger — FTS wird manuell beim Bulk-Load befüllt.
# Bei Einzelupdates müsste man Trigger ergänzen, aber für einen
# Read-Only-Cache reicht manuelles Rebuild.
_CREATE_FTS_TRIGGERS = ""

_CREATE_META_TABLE = """
CREATE TABLE IF NOT EXISTS cache_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_laws_sr_number ON laws(sr_number);
CREATE INDEX IF NOT EXISTS idx_laws_abbreviation ON laws(abbreviation);
CREATE INDEX IF NOT EXISTS idx_laws_is_active ON laws(is_active);
"""


# ---------------------------------------------------------------------------
# Cache-Klasse
# ---------------------------------------------------------------------------


class LawCache:
    """SQLite-basierter Cache für Zürcher Gesetzesdaten.

    Verwendet FTS5 für Volltextsuche und unterstützt:
    - Volltextsuche mit Ranking (BM25)
    - Suche nach Ordnungsnummer (sr_number)
    - Suche nach Abkürzung (VSG, LPG, etc.)
    - Filter nach aktiv/inaktiv
    - Prefix-Filter (z.B. "412." für Bildungsrecht)
    """

    def __init__(self, db_dir: Path | None = None) -> None:
        self.db_dir = db_dir or DEFAULT_DB_DIR
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.db_dir / DB_FILENAME
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Erstellt eine neue Verbindung mit Row-Factory."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        """Erstellt Tabellen und FTS-Index."""
        conn = self._get_conn()
        try:
            conn.executescript(
                _CREATE_LAWS_TABLE
                + _CREATE_META_TABLE
                + _CREATE_INDEXES
            )
            # FTS separat (VIRTUAL TABLE)
            try:
                conn.execute(_CREATE_FTS_TABLE)
            except sqlite3.OperationalError:
                pass  # Existiert bereits
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # HuggingFace Daten laden
    # ------------------------------------------------------------------

    def load_from_huggingface(self, force: bool = False) -> dict:
        """Lädt ZH-Gesetze von HuggingFace und füllt den Cache.

        Args:
            force: Cache auch wenn aktuell (< 24h alt).

        Returns:
            Dict mit 'loaded', 'total', 'duration_s'.
        """
        if not force and self.is_fresh():
            count = self.count_laws()
            return {"loaded": 0, "total": count, "duration_s": 0, "status": "cache_fresh"}

        start = time.monotonic()

        try:
            from datasets import load_dataset
        except ImportError:
            return {
                "loaded": 0, "total": 0, "duration_s": 0,
                "status": "error",
                "message": "Das Paket 'datasets' ist nicht installiert. Bitte 'pip install datasets' ausführen.",
            }

        try:
            ds = load_dataset(HF_DATASET, split=HF_SPLIT)
        except Exception as e:
            return {
                "loaded": 0, "total": 0, "duration_s": 0,
                "status": "error",
                "message": f"HuggingFace-Download fehlgeschlagen: {e}",
            }

        # Filter: nur Kanton Zürich, Deutsch
        zh_laws = [
            row for row in ds
            if row.get("canton") == "zh" and row.get("language", "de") == "de"
        ]

        conn = self._get_conn()
        try:
            # Alte Daten löschen und FTS neu aufbauen
            conn.execute("DELETE FROM laws")
            conn.execute("DROP TABLE IF EXISTS laws_fts")
            conn.execute(_CREATE_FTS_TABLE)

            for row in zh_laws:
                conn.execute(
                    """INSERT OR REPLACE INTO laws
                    (uuid, title, short_desc, abbreviation, sr_number, is_active,
                     pdf_url, html_url, pdf_content, html_content,
                     version_since, family_since, canton, language)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        row.get("uuid", ""),
                        row.get("title", ""),
                        row.get("short", ""),
                        row.get("abbreviation", ""),
                        row.get("sr_number", ""),
                        1 if row.get("is_active", True) else 0,
                        row.get("pdf_url", ""),
                        row.get("html_url", ""),
                        row.get("pdf_content", ""),
                        row.get("html_content", ""),
                        row.get("version_active_since", ""),
                        row.get("family_active_since", ""),
                        "zh",
                        "de",
                    ),
                )

            # FTS-Index befüllen
            # WICHTIG: pdf_content bevorzugen, da html_content im
            # rcds/swiss_legislation Dataset teils falsch zugeordnet ist.
            from openlex_mcp.law_parser import clean_text
            rows = conn.execute(
                "SELECT uuid, title, short_desc, abbreviation, sr_number, "
                "html_content, pdf_content FROM laws"
            ).fetchall()
            for row in rows:
                # pdf_content ist zuverlässiger als html_content
                raw_content = row["pdf_content"] or row["html_content"] or ""
                cleaned = clean_text(raw_content) if raw_content else ""
                conn.execute(
                    "INSERT INTO laws_fts(uuid, title, short_desc, abbreviation, "
                    "sr_number, body) VALUES (?, ?, ?, ?, ?, ?)",
                    (row["uuid"], row["title"], row["short_desc"],
                     row["abbreviation"], row["sr_number"], cleaned),
                )

            # Update-Zeitstempel
            conn.execute(
                "INSERT OR REPLACE INTO cache_meta (key, value) VALUES (?, ?)",
                ("last_update", str(int(time.time()))),
            )
            conn.commit()

        finally:
            conn.close()

        duration = round(time.monotonic() - start, 1)
        logger.info("Cache geladen: %d ZH-Gesetze in %.1fs", len(zh_laws), duration)

        return {
            "loaded": len(zh_laws),
            "total": len(zh_laws),
            "duration_s": duration,
            "status": "ok",
        }

    # ------------------------------------------------------------------
    # Cache-Status
    # ------------------------------------------------------------------

    def is_fresh(self, max_age_hours: int = 24) -> bool:
        """Prüft ob der Cache aktuell genug ist."""
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT value FROM cache_meta WHERE key = 'last_update'"
            ).fetchone()
            if not row:
                return False
            last_update = int(row["value"])
            age_hours = (time.time() - last_update) / 3600
            return age_hours < max_age_hours
        finally:
            conn.close()

    def count_laws(self) -> int:
        """Anzahl Gesetze im Cache."""
        conn = self._get_conn()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM laws").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def ensure_loaded(self) -> dict:
        """Stellt sicher, dass der Cache gefüllt ist. Lädt bei Bedarf."""
        if self.count_laws() == 0:
            return self.load_from_huggingface(force=True)
        return {"loaded": 0, "total": self.count_laws(), "status": "already_loaded"}

    # ------------------------------------------------------------------
    # Suche
    # ------------------------------------------------------------------

    def search_fulltext(
        self,
        query: str,
        *,
        active_only: bool = True,
        sr_prefix: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Volltextsuche mit FTS5 und BM25-Ranking.

        Args:
            query: Suchbegriff(e).
            active_only: Nur aktive Gesetze.
            sr_prefix: Filter nach Ordnungsnummer-Prefix (z.B. '412' für Bildung).
            limit: Max. Ergebnisse.

        Returns:
            Liste von Law-Dicts mit 'rank'-Feld (niedriger = relevanter).
        """
        conn = self._get_conn()
        try:
            # FTS5-Query mit BM25-Ranking
            sql = """
                SELECT laws.*, bm25(laws_fts) as rank,
                       snippet(laws_fts, 5, '**', '**', '...', 40) as snippet
                FROM laws_fts
                JOIN laws ON laws.uuid = laws_fts.uuid
                WHERE laws_fts MATCH ?
            """
            params: list = [query]

            if active_only:
                sql += " AND laws.is_active = 1"
            if sr_prefix:
                sql += " AND laws.sr_number LIKE ?"
                params.append(f"{sr_prefix}%")

            sql += " ORDER BY rank LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

        except sqlite3.OperationalError as e:
            # FTS-Syntax-Fehler → Fallback auf einfache LIKE-Suche
            logger.warning("FTS5-Fehler, Fallback auf LIKE: %s", e)
            return self._search_like(query, active_only=active_only,
                                     sr_prefix=sr_prefix, limit=limit)
        finally:
            conn.close()

    def _search_like(
        self,
        query: str,
        *,
        active_only: bool = True,
        sr_prefix: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Fallback-Suche mit LIKE (wenn FTS5 fehlschlägt)."""
        conn = self._get_conn()
        try:
            sql = """
                SELECT *, 0 as rank, '' as snippet FROM laws
                WHERE (title LIKE ? OR pdf_content LIKE ? OR html_content LIKE ?
                       OR abbreviation LIKE ? OR short_desc LIKE ?)
            """
            like_q = f"%{query}%"
            params: list = [like_q, like_q, like_q, like_q, like_q]

            if active_only:
                sql += " AND is_active = 1"
            if sr_prefix:
                sql += " AND sr_number LIKE ?"
                params.append(f"{sr_prefix}%")

            sql += " ORDER BY sr_number LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_by_sr_number(self, sr_number: str) -> dict | None:
        """Gesetz anhand der Ordnungsnummer (LS-Nummer) abrufen.

        Args:
            sr_number: z.B. '412.100' (Volksschulgesetz).

        Returns:
            Law-Dict oder None.
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM laws WHERE sr_number = ?", (sr_number,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_abbreviation(self, abbreviation: str) -> dict | None:
        """Gesetz anhand der Abkürzung abrufen.

        Args:
            abbreviation: z.B. 'VSG' (Volksschulgesetz).

        Returns:
            Law-Dict oder None.
        """
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT * FROM laws WHERE UPPER(abbreviation) = UPPER(?)",
                (abbreviation,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_laws(
        self,
        *,
        active_only: bool = True,
        sr_prefix: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Gesetze auflisten mit optionalem Filter.

        Returns:
            Tuple (laws_list, total_count).
        """
        conn = self._get_conn()
        try:
            where_parts: list[str] = []
            params: list = []

            if active_only:
                where_parts.append("is_active = 1")
            if sr_prefix:
                where_parts.append("sr_number LIKE ?")
                params.append(f"{sr_prefix}%")

            where_sql = " WHERE " + " AND ".join(where_parts) if where_parts else ""

            # Total count
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM laws{where_sql}", params
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            # Results
            params_with_pagination = params + [limit, offset]
            rows = conn.execute(
                f"SELECT * FROM laws{where_sql} ORDER BY sr_number LIMIT ? OFFSET ?",
                params_with_pagination,
            ).fetchall()

            return [dict(row) for row in rows], total
        finally:
            conn.close()

    def get_law_content(self, sr_number: str) -> str:
        """Gibt den Volltext eines Gesetzes zurück (html_content bevorzugt).

        Args:
            sr_number: z.B. '412.100'.

        Returns:
            Volltext als String (oder leer).
        """
        law = self.get_by_sr_number(sr_number)
        if not law:
            return ""
        return law.get("pdf_content") or law.get("html_content") or ""
