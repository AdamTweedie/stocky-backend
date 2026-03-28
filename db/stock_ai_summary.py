from .connection import get_connection
from typing import Optional


def insert_stock_summary(
    short_name: str,
    ai_summary: str,
    tokens_total: int,
    days: int = 3
) -> int:
    """Insert a new AI summary for a stock. Returns the new row id."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO stock_ai_summaries (short_name, ai_summary, tokens_total, days)
            VALUES (?, ?, ?, ?)
        """, (short_name, ai_summary, tokens_total, days))
        conn.commit()
        return cursor.lastrowid


def get_latest_stock_summary(short_name: str) -> Optional[dict]:
    """Get the most recent AI summary for a stock."""
    with get_connection() as conn:
        row = conn.execute("""
            SELECT * FROM stock_ai_summaries
            WHERE short_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (short_name,)).fetchone()
        return dict(row) if row else None


def get_stock_summary_history(short_name: str, limit: int = 10) -> list[dict]:
    """Get all AI summaries for a stock, most recent first."""
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM stock_ai_summaries
            WHERE short_name = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (short_name, limit)).fetchall()
        return [dict(row) for row in rows]