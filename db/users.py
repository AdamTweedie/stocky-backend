# db/users.py
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
import bcrypt
from .connection import get_connection

# ─────────────────────────────────────────
# REGISTER / CREATE
# ─────────────────────────────────────────

def create_user_email(
    email: str,
    name: str,
    password: str,
) -> int | None:
    """Register a new user with email/password. Returns new id or None if email exists."""
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            return None

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cursor = conn.execute("""
            INSERT INTO users (email, name, password_hash)
            VALUES (?, ?, ?)
        """, (email, name, password_hash))
        conn.commit()
        return cursor.lastrowid


def create_user_google(
    google_id: str,
    email: str,
    name: str,
    avatar_url: str = None,
) -> int:
    """
    Upsert a Google OAuth user. If email exists, links google_id to existing account.
    Returns the user id.
    """
    with get_connection() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            conn.execute("""
                UPDATE users SET google_id = ?, avatar_url = ?, last_login_at = ?
                WHERE email = ?
            """, (google_id, avatar_url, _now(), email))
            conn.commit()
            return existing["id"]

        cursor = conn.execute("""
            INSERT INTO users (google_id, email, name, avatar_url, email_verified)
            VALUES (?, ?, ?, ?, 1)
        """, (google_id, email, name, avatar_url))
        conn.commit()
        return cursor.lastrowid

# ─────────────────────────────────────────
# LOGIN / SESSION
# ─────────────────────────────────────────

def login_email(email: str, password: str) -> Optional[str]:
    """
    Verify email/password and issue a session token.
    Returns session token if valid, None if invalid credentials.
    """
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)
        ).fetchone()

        if not user or not user["password_hash"]:
            return None
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return None

        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        conn.execute("""
            UPDATE users SET session_token = ?, session_expires_at = ?, last_login_at = ?
            WHERE id = ?
        """, (token, expires, _now(), user["id"]))
        conn.commit()
        return token
    

def login_google(user_id: int)-> str:
    """Issue a session token for a Google OAuth user."""
    token = secrets.token_urlsafe(32)
    expires = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    with get_connection() as conn:
        conn.execute("""
            UPDATE users SET session_token = ?, session_expires_at = ?, last_login_at = ?
            WHERE id = ?
        """, (token, expires, _now(), user_id))
        conn.commit()
    return token


def get_user_by_session(session_token: str) -> Optional[dict]:
    """Validate session token and return user if valid and not expired."""
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE session_token = ? AND is_active = 1", (session_token,)
        ).fetchone()

        if not user:
            return None
        if user["session_expires_at"] and user["session_expires_at"] < _now():
            return None  # expired

        return dict(user)


def logout(session_token: str) -> bool:
    """Invalidate a session token."""
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE users SET session_token = NULL, session_expires_at = NULL
            WHERE session_token = ?
        """, (session_token,))
        conn.commit()
        return cursor.rowcount > 0

# ─────────────────────────────────────────
# GET
# ─────────────────────────────────────────

def get_user_by_id(user_id: int) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None


def get_user_by_google_id(google_id: str) -> Optional[dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()
        return dict(row) if row else None


def get_users_by_tier(tier: str) -> list[dict]:
    """Fetch all users on a given tier: 'free', 'pro', 'enterprise'."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE tier = ? AND is_active = 1", (tier,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_all_users(include_inactive: bool = False) -> list[dict]:
    with get_connection() as conn:
        query = "SELECT * FROM users" if include_inactive else "SELECT * FROM users WHERE is_active = 1"
        rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]

# ─────────────────────────────────────────
# UPDATE — PROFILE
# ─────────────────────────────────────────

def update_user_profile(user_id: int, **fields) -> bool:
    """
    Update basic profile fields.

    Usage:
        update_user_profile(1, name="Alice", avatar_url="https://...")
    """
    allowed = {"name", "email", "avatar_url"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return False

    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]

    with get_connection() as conn:
        cursor = conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return cursor.rowcount > 0


def update_password(user_id: int, new_password: str) -> bool:
    """Hash and update a user's password."""
    password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0


def verify_email(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount > 0

# ─────────────────────────────────────────
# UPDATE — PASSWORD RESET
# ─────────────────────────────────────────

def set_reset_token(email: str) -> Optional[str]:
    """
    Generate and store a password reset token valid for 1 hour.
    Returns the token to be emailed to the user, or None if email not found.
    """
    with get_connection() as conn:
        user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            return None

        token = secrets.token_urlsafe(32)
        expires = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        conn.execute("""
            UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE id = ?
        """, (token, expires, user["id"]))
        conn.commit()
        return token


def reset_password(reset_token: str, new_password: str) -> bool:
    """Validate reset token, update password, and clear the token."""
    with get_connection() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE reset_token = ?", (reset_token,)
        ).fetchone()

        if not user:
            return False
        if user["reset_token_expires"] < _now():
            return False  # token expired

        password_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        conn.execute("""
            UPDATE users
            SET password_hash = ?, reset_token = NULL, reset_token_expires = NULL
            WHERE id = ?
        """, (password_hash, user["id"]))
        conn.commit()
        return True

# ─────────────────────────────────────────
# UPDATE — TIER & SUBSCRIPTION
# ─────────────────────────────────────────

def update_subscription(
    user_id: int,
    tier: str,
    subscription_id: str,
    renewal_date: str,
) -> bool:
    """Upgrade or change a user's subscription tier."""
    start = _now()
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE users
            SET tier = ?, tier_status = 'active', subscription_id = ?,
                subscription_start = ?, subscription_renewal = ?, subscription_end = NULL
            WHERE id = ?
        """, (tier, subscription_id, start, renewal_date, user_id))
        conn.commit()
        return cursor.rowcount > 0


def cancel_subscription(user_id: int, access_until: str) -> bool:
    """
    Mark subscription as cancelled. User retains access until access_until date.
    
    Usage:
        cancel_subscription(1, "2025-02-01T00:00:00Z")
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE users
            SET tier_status = 'cancelled', subscription_end = ?
            WHERE id = ?
        """, (access_until, user_id))
        conn.commit()
        return cursor.rowcount > 0


def downgrade_expired_subscriptions() -> int:
    """
    Downgrade any cancelled users whose access period has expired to free tier.
    Call this on a schedule (e.g. daily cron job).
    Returns number of users downgraded.
    """
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE users
            SET tier = 'free', tier_status = 'active',
                subscription_id = NULL, subscription_end = NULL
            WHERE tier_status = 'cancelled' AND subscription_end < ?
        """, (_now(),))
        conn.commit()
        return cursor.rowcount

# ─────────────────────────────────────────
# UPDATE — AI TOKENS
# ─────────────────────────────────────────

TIER_TOKEN_LIMITS = {
    "free":       10_000,
    "pro":        100_000,
    "enterprise": 1_000_000,
}

def increment_ai_tokens(user_id: int, tokens_used: int) -> dict:
    """
    Increment a user's AI token usage.
    Returns { "allowed": bool, "used": int, "limit": int }
    """
    with get_connection() as conn:
        user = conn.execute(
            "SELECT tier, ai_tokens_used FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            return {"allowed": False, "used": 0, "limit": 0}

        limit = TIER_TOKEN_LIMITS.get(user["tier"], 0)
        new_total = user["ai_tokens_used"] + tokens_used

        conn.execute(
            "UPDATE users SET ai_tokens_used = ? WHERE id = ?", (new_total, user_id)
        )
        conn.commit()
        return {"allowed": new_total <= limit, "used": new_total, "limit": limit}


def reset_ai_tokens(user_id: int) -> bool:
    """Reset a user's token counter, e.g. on billing cycle renewal."""
    with get_connection() as conn:
        cursor = conn.execute("""
            UPDATE users SET ai_tokens_used = 0, ai_tokens_reset_at = ? WHERE id = ?
        """, (_now(), user_id))
        conn.commit()
        return cursor.rowcount > 0


def get_token_usage(user_id: int) -> Optional[dict]:
    """Return a user's current token usage and their tier limit."""
    with get_connection() as conn:
        user = conn.execute(
            "SELECT tier, ai_tokens_used, ai_tokens_reset_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not user:
            return None
        limit = TIER_TOKEN_LIMITS.get(user["tier"], 0)
        return {
            "used":       user["ai_tokens_used"],
            "limit":      limit,
            "remaining":  max(0, limit - user["ai_tokens_used"]),
            "reset_at":   user["ai_tokens_reset_at"],
        }

# ─────────────────────────────────────────
# UPDATE — ACCOUNT STATUS
# ─────────────────────────────────────────

def deactivate_user(user_id: int) -> bool:
    """Soft-disable a user account without deleting it."""
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def reactivate_user(user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET is_active = 1 WHERE id = ?", (user_id,)
        )
        conn.commit()
        return cursor.rowcount > 0


def set_admin(user_id: int, is_admin: bool) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            "UPDATE users SET is_admin = ? WHERE id = ?", (int(is_admin), user_id)
        )
        conn.commit()
        return cursor.rowcount > 0

# ─────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────

def delete_user(user_id: int) -> bool:
    """Hard delete. Prefer deactivate_user() in most cases."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0

# ─────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()