from .connection import get_connection
from datetime import datetime, timezone


def aggregate_daily_sentiment(date: str = None) -> int:
    """
    Aggregate sentiment scores from news table into stock_sentiment_history.
    Defaults to today if no date provided.
    Returns number of stocks aggregated.
    """
    if date is None:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT OR REPLACE INTO stock_sentiment_history 
                (short_name, date, avg_sentiment, article_count, positive_count, negative_count, neutral_count)
            SELECT 
                short_name,
                ? as date,
                AVG(sentiment) as avg_sentiment,
                COUNT(*) as article_count,
                SUM(CASE WHEN sentiment > 0.2 THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment < -0.2 THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment BETWEEN -0.2 AND 0.2 THEN 1 ELSE 0 END) as neutral_count
            FROM news
            WHERE date(publish_time) = ?
            AND sentiment IS NOT NULL
            GROUP BY short_name
        """, (date, date))
        conn.commit()
        return cursor.rowcount


def get_sentiment_history(short_name: str, days: int = 30) -> list[dict]:
    """
    Fetch sentiment history for a stock for the last N days.
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM stock_sentiment_history
            WHERE short_name = ?
            ORDER BY date DESC
            LIMIT ?
        """, (short_name, days)).fetchall()
        return [dict(row) for row in rows]


def get_sentiment_history_range(short_name: str, start_date: str, end_date: str) -> list[dict]:
    """
    Fetch sentiment history for a stock between two dates.

    Usage:
        get_sentiment_history_range("AAPL", "2026-01-01", "2026-03-22")
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM stock_sentiment_history
            WHERE short_name = ?
            AND date BETWEEN ? AND ?
            ORDER BY date ASC
        """, (short_name, start_date, end_date)).fetchall()
        return [dict(row) for row in rows]