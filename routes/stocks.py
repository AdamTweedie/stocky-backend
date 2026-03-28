# routes/stocks.py
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from typing import List, Optional
from db import (get_stocks_by_search, 
                get_stock_by_short_name,
                get_stocks_by_filter,
                get_popular_stocks, 
                get_quote_by_symbol,
                is_free,
                )
from jobs import update_single_stock_price, get_or_fetch_quote


router = APIRouter(prefix="/stocks", tags=["Stocks"])


class StockResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    currencyCode: Optional[str] = None
    type: Optional[str] = None
    industry: Optional[str] = None
    price: Optional[float] = None
    change: Optional[float] = None
    changePercent: Optional[float] = None
    inFreeTier: Optional[bool] = None
    inUse: Optional[bool] = None


class QuoteResponse(BaseModel):
    symbol: str
    price: Optional[float] = None
    change: Optional[float] = None
    changePercent: Optional[float] = None
    currencyCode: Optional[str] = None


class StockListResponse(BaseModel):
    results: List[StockResponse]


class QuoteListResponse(BaseModel):
    results: List[QuoteResponse]


def db_to_stock(item: dict) -> StockResponse:
    return StockResponse(
        symbol=item["short_name"],
        name=item["name"],
        currencyCode=item["currency_code"],
        type=item["type"],
        industry=item["industry"],
        price=item["price"],
        change=item["price_change"],
        changePercent=item["price_change_percent"],
        inFreeTier=bool(item["in_free_tier"]),
        inUse=bool(item["in_use"])
    )


@router.get("/popular", response_model=StockListResponse)
def get_popular_stocks_route():
    free = get_stocks_by_filter(inFreeTier=True)
    popular = get_popular_stocks()

    # combine, with free stocks first, avoiding duplicates
    free_symbols = {s["short_name"] for s in free}
    combined = free + [s for s in popular if s["short_name"] not in free_symbols]

    return StockListResponse(results=[db_to_stock(s) for s in combined])


@router.get("/free", response_model=StockListResponse)
def get_free_stocks():
    raw = get_stocks_by_filter(inFreeTier=True)
    return StockListResponse(results=[db_to_stock(s) for s in raw])


@router.get("/is_free")
def search_stocks(q: str = Query(..., min_length=1)):
    free = is_free(q)
    return {"is_free":f"{free}"}


@router.get("/search", response_model=StockListResponse)
def search_stocks(q: str = Query(..., min_length=1)):
    raw = get_stocks_by_search(q.lower())
    return StockListResponse(results=[db_to_stock(s) for s in raw])


@router.get("/quotes", response_model=QuoteListResponse)
def get_quotes(q: str = Query(...)):
    symbols = [s.strip() for s in q.split(",")]
    quotes = []

    for sym in symbols:
        item = get_or_fetch_quote(sym)
        if item:
            quotes.append(QuoteResponse(
                symbol=item["short_name"],
                price=item["price"],
                change=item["price_change"],
                changePercent=item["price_change_percent"],
                currencyCode=item["currency_code"]
            ))
        else:
            quotes.append(QuoteResponse(symbol=sym, price=None, change=None, changePercent=None, currencyCode=None))

    return QuoteListResponse(results=quotes)

