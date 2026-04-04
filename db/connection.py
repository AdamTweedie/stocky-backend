import sqlite3


DB_PATH = "stocky.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Enable dict-like access to rows
    return conn

# ------------ CREATE TABLE --------------
def create_tables():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                short_name            TEXT NOT NULL,
                name                  TEXT NOT NULL,
                currency_code         TEXT NOT NULL,
                type                  TEXT NOT NULL,
                industry              TEXT,
                price                 REAL,
                price_change          REAL,
                price_change_percent  REAL,
                in_free_tier          INTEGER NOT NULL DEFAULT 0,
                in_use                INTEGER NOT NULL DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                short_name           TEXT NOT NULL,
                source               TEXT NOT NULL,
                source_url           TEXT,
                source_country       TEXT,
                source_type          TEXT NOT NULL,
                lang                 TEXT,
                publish_time         TEXT NOT NULL,
                url                  TEXT NOT NULL,
                image                TEXT,
                title                TEXT NOT NULL,
                description          TEXT,
                sentiment            REAL,
                AI_summary           TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_sentiment_history (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                short_name   TEXT NOT NULL,
                date         TEXT NOT NULL,                   
                avg_sentiment     REAL,                        
                article_count     INTEGER,                     
                positive_count    INTEGER,                     
                negative_count    INTEGER,                     
                neutral_count     INTEGER,                     
                UNIQUE(short_name, date)
            )                     
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),

            -- Google OAuth (nullable if using email/password)
            google_id             TEXT UNIQUE,
            avatar_url            TEXT,

            -- Shared fields
            email                 TEXT NOT NULL UNIQUE,
            email_verified        INTEGER NOT NULL DEFAULT 0,
            name                  TEXT,

            -- Email/password only (nullable if using Google)
            password_hash         TEXT,
            reset_token           TEXT UNIQUE,
            reset_token_expires   TEXT,

            -- Session
            session_token         TEXT UNIQUE,
            session_expires_at    TEXT,
            last_login_at         TEXT,

            -- Tier & subscription
            tier                  TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free', 'pro', 'enterprise')),
            tier_status           TEXT NOT NULL DEFAULT 'active' CHECK(tier_status IN ('active', 'cancelled', 'past_due', 'paused')),
            subscription_id       TEXT UNIQUE,          -- Stripe/payment provider subscription ID
            subscription_start    TEXT,
            subscription_renewal  TEXT,
            subscription_end      TEXT,                 -- set when cancelled, access valid until this date

            -- AI token usage
            ai_tokens_used        INTEGER NOT NULL DEFAULT 0,
            ai_tokens_reset_at    TEXT,                 -- when the usage counter last reset (e.g. billing cycle)

            -- Account status
            is_active             INTEGER NOT NULL DEFAULT 1,   -- soft ban/disable without deleting
            is_admin              INTEGER NOT NULL DEFAULT 0
        )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_stocks (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                user_id      INTEGER NOT NULL,
                short_name   TEXT NOT NULL,
                position     INTEGER NOT NULL DEFAULT 0,        -- for ordering
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, short_name)                     -- prevent duplicate follows
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_industries (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                user_id      INTEGER NOT NULL,
                industry     TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, industry)                       -- prevent duplicate follows
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS stock_ai_summaries (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                short_name    TEXT NOT NULL,
                ai_summary    TEXT NOT NULL,
                tokens_total  INTEGER NOT NULL,
                days          INTEGER NOT NULL DEFAULT 3
            )
        """)


        conn.commit()
