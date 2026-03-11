#STOCKY
##Background




The key separation of concerns:

`services/` — only talks to external APIs, returns raw/cleaned data. Knows nothing about your DB.

`db/` — only talks to SQLite. Knows nothing about external APIs or routes.

`routes/` — only handles HTTP requests/responses. Calls services and db, never directly calls external APIs itself.

`jobs/` — orchestrates services and db together, e.g. refresh_news.py calls news_service.py to fetch, then db.insert_news() to store.

And `config.py` is where all your API keys and environment variables live, imported by services and never hardcoded anywhere else.

External API → services/ → jobs/ → db/
Frontend     → routes/   → db/
