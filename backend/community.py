"""
Community feature — user-submitted weather reports stored in SQLite.
Schema:
  reports(id, lat, lon, city, condition, description, photo_url,
          username, created_at)
"""

import os
import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("COMMUNITY_DB", "data/community.db")


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

@contextmanager
def _conn():
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    """Create tables if they don't exist yet."""
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lat         REAL    NOT NULL,
                lon         REAL    NOT NULL,
                city        TEXT    DEFAULT '',
                condition   TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                photo_url   TEXT    DEFAULT '',
                username    TEXT    DEFAULT 'Anonymous',
                created_at  TEXT    NOT NULL
            )
        """)
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_reports_location
            ON reports (lat, lon)
        """)
        con.execute("""
            CREATE INDEX IF NOT EXISTS idx_reports_created
            ON reports (created_at DESC)
        """)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_report(
    lat: float,
    lon: float,
    condition: str,
    description: str = "",
    city: str = "",
    photo_url: str = "",
    username: str = "Anonymous",
) -> dict:
    """Insert a new community weather report."""
    now = datetime.now(timezone.utc).isoformat()
    with _conn() as con:
        cur = con.execute(
            """
            INSERT INTO reports (lat, lon, city, condition, description,
                                 photo_url, username, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (lat, lon, city, condition, description, photo_url, username, now),
        )
        report_id = cur.lastrowid
    return get_report(report_id)


def get_report(report_id: int) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
    return dict(row) if row else None


def get_nearby_reports(
    lat: float,
    lon: float,
    radius_deg: float = 1.0,
    limit: int = 20,
) -> list[dict]:
    """
    Return reports within an approximate bounding box (radius_deg degrees).
    Sorted by newest first.
    """
    with _conn() as con:
        rows = con.execute(
            """
            SELECT * FROM reports
            WHERE lat BETWEEN ? AND ?
              AND lon BETWEEN ? AND ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (
                lat - radius_deg, lat + radius_deg,
                lon - radius_deg, lon + radius_deg,
                limit,
            ),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_reports(limit: int = 50) -> list[dict]:
    """Return the most recent reports globally."""
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM reports ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_report(report_id: int) -> bool:
    with _conn() as con:
        cur = con.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    return cur.rowcount > 0
