# routes/stocks.py
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from db import get_news_by_short_name

router = APIRouter(prefix="/news")


class NewsResponse(BaseModel):
    # NOT NULL in db - always present
    id: int
    short_name: str
    source: str
    publish_time: str
    url: str
    title: str

    # nullable in db - can be None
    source_url: Optional[str] = None
    source_country: Optional[str] = None
    lang: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    sentiment: Optional[float] = None
    ai_summary: Optional[str] = None

class NewsListResponse(BaseModel):
    results: List[NewsResponse]


def db_to_news(item: dict) -> NewsResponse:
    return NewsResponse(
        id=item["id"],
        short_name=item["short_name"],
        source=item["source"],
        publish_time=item["publish_time"],
        url=item["url"],
        title=item["title"],
        source_url=item["source_url"],
        source_country=item["source_country"],
        lang=item["lang"],
        image=item["image"],
        description=item["description"],
        sentiment=item["sentiment"],
        ai_summary=item["AI_summary"]
    )


@router.get("/symbol", response_model=NewsListResponse)
def get_news_by_symbol(
    q: str = Query(...),
    since: str = Query(None)  # ISO 8601 timestamp e.g. "2026-03-22T10:00:00"
    ):

    symbols = [s.strip() for s in q.split(",")]
    news = []
    for sym in symbols:
        items = get_news_by_short_name(short_name=sym, since=since)
        for item in items:
            news.append(db_to_news(item))
    return NewsListResponse(results=news)

