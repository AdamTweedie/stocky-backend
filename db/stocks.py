from .connection import get_connection
from typing import Optional


# -------------- INSERT ----------------
def insert_stock(
    shortName: str,
    name: str,
    type: str,
    price: float = None,
    priceChange: float = None,
    priceChangePercent: float = None,
    inFreeTier: bool = False,
    inUse: bool = False,
) -> int | None:
    
    """Insert a new stock. Returns the new row's id, or None if short_name already exists."""
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM stocks WHERE short_name = ?", (shortName,)).fetchone()
        if existing:
            return None

        cursor = conn.execute("""
            INSERT INTO stocks (short_name, name, type, price, price_change, price_change_percent, in_free_tier, in_use)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (shortName, name, type, price, priceChange, priceChangePercent, int(inFreeTier), int(inUse)))
        conn.commit()
        return cursor.lastrowid
    

def bulk_insert_stocks(stocks: list[dict]) -> int:
    """Insert many stocks in a single transaction. Returns count inserted."""
    with get_connection() as conn:
        count = 0
        for stock in stocks:
            existing = conn.execute(
                "SELECT id FROM stocks WHERE short_name = ?", (stock["shortName"],)
            ).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO stocks (short_name, name, type)
                    VALUES (?, ?, ?)
                """, (stock["shortName"], stock["name"], stock["type"]))
                count += 1
        conn.commit()  # one single commit at the end
    return count
    

# -------------- GET ----------------
def get_all_stocks():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM stocks").fetchall()
        return [dict(row) for row in rows]
    

def get_stock_by_short_name(short_name: str) -> Optional[dict]:
    """Fetch a single stock by shortName."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM stocks WHERE short_name = ?", (short_name,)).fetchone()
        return dict(row) if row else None
    

def get_stocks_by_filter(
    type: str = None,
    industry: str = None,
    inFreeTier: bool = None,
    inUse: bool = None,
) -> list[dict]:
    """Fetch stocks with optional filters."""
    query = "SELECT * FROM stocks WHERE 1=1"
    params = []

    if type is not None:
        query += " AND type = ?"
        params.append(type)
    if industry is not None:
        query += " AND industry = ?"
        params.append(industry)
    if inFreeTier is not None:
        query += " AND in_free_tier = ?"
        params.append(int(inFreeTier))
    if inUse is not None:
        query += " AND in_use = ?"
        params.append(int(inUse))

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    

def get_stocks_by_search(query: str) -> list[dict]:
    """
    Return all stocks whose short_name or name starts with the query string.
    Case-insensitive.

    Usage:
        search_stocks("app") → returns Apple, APP, etc.
    """
    pattern = f"{query}%"
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM stocks
            WHERE short_name LIKE ? OR name LIKE ?
            ORDER BY short_name ASC
        """, (pattern, pattern)).fetchall()
        return [dict(row) for row in rows]


def get_stocks_table_size() -> int:
    """Return the number of rows in the stocks table."""
    with get_connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS count FROM stocks").fetchone()
        return row["count"] if row else 0
    

# -------------- UPDATE ----------------
def update_stock(short_name: str, **fields) -> bool:
    """
    Update any fields on an stock by shortName.
    
    Usage:
        update_stock("BTC", price=99.9, inUse=True)
    """
    if not fields:
        return False

    for key in ("in_free_tier", "in_use"):
        if key in fields and isinstance(fields[key], bool):
            fields[key] = int(fields[key])

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [short_name]

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE stocks SET {set_clause} WHERE short_name = ?", values
        )
        conn.commit()
        return cursor.rowcount > 0
    

# -------------- DELETE ----------------
def delete_stock(short_name: str) -> bool:
    """Delete an stock by shortName. Returns True if an stock was deleted."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM stocks WHERE short_name = ?", (short_name,))
        conn.commit()
        return cursor.rowcount > 0
    