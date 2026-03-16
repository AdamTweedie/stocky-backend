from .connection import get_connection


# ─────────────────────────────────────────
# USER STOCKS
# ─────────────────────────────────────────
def follow_stock(user_id: int, short_name: str) -> bool:
    """Add a stock to a user's followed list. Returns False if already following."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM user_stocks WHERE user_id = ? AND short_name = ?",
            (user_id, short_name)
        ).fetchone()
        if existing:
            return False

        # Place at end of list by default
        max_pos = conn.execute(
            "SELECT MAX(position) FROM user_stocks WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
        position = (max_pos + 1) if max_pos is not None else 0

        conn.execute(
            "INSERT INTO user_stocks (user_id, short_name, position) VALUES (?, ?, ?)",
            (user_id, short_name, position)
        )
        conn.commit()
        return True


def unfollow_stock(user_id: int, short_name: str) -> bool:
    """Remove a stock from a user's followed list."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM user_stocks WHERE user_id = ? AND short_name = ?",
            (user_id, short_name)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_followed_stocks(user_id: int) -> list[dict]:
    """Get all stocks a user follows, in their saved order."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM user_stocks WHERE user_id = ? ORDER BY position ASC",
            (user_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def reorder_stocks(user_id: int, ordered_short_names: list[str]) -> bool:
    """
    Update the order of a user's followed stocks.

    Usage:
        reorder_stocks(1, ["AAPL", "TSLA", "BTC"])
    """
    with get_connection() as conn:
        for position, short_name in enumerate(ordered_short_names):
            conn.execute("""
                UPDATE user_stocks SET position = ?
                WHERE user_id = ? AND short_name = ?
            """, (position, user_id, short_name))
        conn.commit()
        return True
    

def get_popular_stocks(limit: int = 10) -> list[dict]:
    """
    Returns the most followed stocks across all users, with full stock details.
    """
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT s.*, COUNT(uf.user_id) as follower_count
            FROM user_stocks uf
            JOIN stocks s ON uf.short_name = s.short_name
            GROUP BY uf.short_name
            ORDER BY follower_count DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(row) for row in rows]

# ─────────────────────────────────────────
# USER INDUSTRIES
# ─────────────────────────────────────────

def follow_industry(user_id: int, industry: str) -> bool:
    """Add an industry to a user's followed list. Returns False if already following."""
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM user_industries WHERE user_id = ? AND industry = ?",
            (user_id, industry)
        ).fetchone()
        if existing:
            return False

        conn.execute(
            "INSERT INTO user_industries (user_id, industry) VALUES (?, ?)",
            (user_id, industry)
        )
        conn.commit()
        return True


def unfollow_industry(user_id: int, industry: str) -> bool:
    """Remove an industry from a user's followed list."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM user_industries WHERE user_id = ? AND industry = ?",
            (user_id, industry)
        )
        conn.commit()
        return cursor.rowcount > 0


def get_followed_industries(user_id: int) -> list[str]:
    """Get all industries a user follows."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT industry FROM user_industries WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,)
        ).fetchall()
        return [row["industry"] for row in rows]


def get_user_feed_filters(user_id: int) -> dict:
    """
    Convenience function — returns both followed stocks and industries in one call.
    Useful for building a personalised news/data feed.

    Returns:
        { "stocks": ["AAPL", "TSLA"], "industries": ["Technology", "Energy"] }
    """
    return {
        "stocks":     [r["short_name"] for r in get_followed_stocks(user_id)],
        "industries": get_followed_industries(user_id),
    }


# --------------- GET ---------------
def get_active_short_names() -> set[str]:
    """
    Return a unique set of all short_names that should be refreshed:
    - any stock followed by at least one user
    - any stock in the free tier
    """
    with get_connection() as conn:
        followed = conn.execute(
            "SELECT DISTINCT short_name FROM user_stocks"
        ).fetchall()

        free_tier = conn.execute(
            "SELECT short_name FROM stocks WHERE in_free_tier = 1"
        ).fetchall()

        return {row["short_name"] for row in followed} | {row["short_name"] for row in free_tier}