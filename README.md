# Stocky Backend

A Python/FastAPI backend for Stocky — a financial news and sentiment analysis platform that aggregates stock market news, analyses sentiment, and delivers AI-powered summaries via a tiered subscription model.

---

## Features

- **Stock price tracking** across global exchanges with multi-source fallback (Alpha Vantage, yFinance, stockprices.dev)
- **News aggregation** from GNews API and RSS feeds (Bloomberg, Reuters, WSJ, FT and more)
- **NLP sentiment analysis** using VADER on every article
- **AI-powered summaries** via DeepSeek for individual articles and multi-day stock digests
- **Market hours detection** across global exchanges and timezones
- **User authentication** via email/password and Google OAuth2
- **Tiered subscriptions** (free, pro, enterprise) with AI token usage tracking
- **Automated background jobs** for price updates, news refresh and sentiment aggregation

---

## Project Structure

```
stocky-backend/
├── main.py                  # FastAPI app entry point
├── scheduler.py             # Background job scheduler
├── config.py                # API keys and environment variables
├── market_hours.py          # Exchange hours and market open detection
├── dependencies.py          # FastAPI auth dependencies
│
├── db/                      # Database layer
│   ├── __init__.py
│   ├── connection.py        # SQLite connection and table creation
│   ├── stocks.py
│   ├── news.py
│   ├── users.py
│   ├── user_follows.py
│   ├── aggregate_sentiment.py
│   └── stock_ai_summaries.py
│
├── routes/                  # API endpoints
│   ├── __init__.py
│   ├── stocks.py
│   ├── news.py
│   ├── users.py
│   └── auth.py
│
├── services/                # External API integrations
│   ├── __init__.py
│   ├── stock_service.py     # Alpha Vantage, yFinance, stockprices.dev
│   ├── news_service.py      # GNews API and RSS feeds
│   ├── sentiment_service.py # VADER sentiment analysis
│   └── ai_service.py        # DeepSeek AI summaries
│
└── jobs/                    # Background tasks
    ├── __init__.py
    ├── refresh_stocks.py    # Stock price updates
    ├── refresh_news.py      # News fetching and insertion
    └── aggregate_sentiment.py # Daily sentiment aggregation
```

---

## Tech Stack

- **Python 3.11+**
- **FastAPI** — REST API framework
- **SQLite** — Database
- **APScheduler** — Background job scheduling
- **yFinance** — Stock price data
- **VADER** — NLP sentiment analysis
- **DeepSeek / OpenAI SDK** — AI article summaries
- **feedparser** — RSS feed parsing
- **bcrypt** — Password hashing
- **pytz** — Timezone-aware market hours

---

## Getting Started

### 1. Clone the repository

```bash
pip install poetry
```

```bash
git clone https://github.com/yourusername/stocky-backend.git
cd stocky-backend
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
poetry install
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
ALPHA_VANTAGE_KEY=your_key_here
GNEWS_KEY=your_key_here
DEEPSEEK_KEY=your_key_here
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

### 5. Initialise the database

```bash
poetry run python -m db.connection
```

### 6. Run the API

```bash
poetry run python main.py
```

API will be available at `http://127.0.0.1:5000`

Swagger UI docs at `http://127.0.0.1:5000/docs`

### 7. Run the scheduler (separate terminal)

```bash
poetry run python scheduler.py
```

---

## API Overview

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register with email and password |
| POST | `/auth/login` | Login and receive session token |
| POST | `/auth/logout` | Invalidate session token |
| GET | `/auth/google` | Initiate Google OAuth |
| GET | `/auth/google/callback` | Google OAuth callback |
| GET | `/auth/me` | Get current user profile |

### Stocks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stocks/free` | Get free tier stocks |
| GET | `/stocks/popular` | Get most followed stocks |
| GET | `/stocks/search?q=` | Search stocks by symbol or name |
| GET | `/stocks/quotes?q=` | Get prices for comma-separated symbols |

### News
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/news/symbol?q=` | Get news for a symbol |
| GET | `/news/symbol?q=&since=` | Get news newer than timestamp |
| GET | `/news/article_ai_summary?q=` | AI summary for article (pro) |
| GET | `/news/stock_ai_summary?q=` | AI summary of recent news (pro) |

### User
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user/profile` | Get user profile |
| PUT | `/user/profile` | Update profile |
| GET | `/user/watchlist` | Get followed stocks |
| POST | `/user/watchlist` | Follow a stock |
| DELETE | `/user/watchlist/{symbol}` | Unfollow a stock |
| GET | `/user/tokens` | Get AI token usage |
| GET | `/user/subscription` | Get subscription details |

---

## Subscription Tiers

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Free tier stocks | ✅ | ✅ | ✅ |
| Follow any stock | ❌ | ✅ | ✅ |
| AI article summaries | ❌ | ✅ | ✅ |
| AI stock digest | ❌ | ✅ | ✅ |
| AI token limit/month | 10,000 | 100,000 | 1,000,000 |

---

## Background Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| `run_refresh_stocks` | Weekly (Monday midnight) | Fetch new instruments from Trading212 |
| `update_stock_prices` | Every 15 minutes | Update prices for active symbols |
| `run_refresh_news` | Every hour | Fetch and insert latest news |
| `run_aggregate_sentiment` | Daily (11pm) | Aggregate daily sentiment scores |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ALPHA_VANTAGE_KEY` | Alpha Vantage API key |
| `GNEWS_KEY` | GNews API key |
| `DEEPSEEK_KEY` | DeepSeek API key |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `TRADING212_SK` | Trading 212 secret key |
| `TRADING212_PK` | Trading 212 public key |


---

## License

Private — all rights reserved.
