from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from db import get_stocks_by_search, get_stock_by_short_name, get_active_short_names

import json
import uvicorn


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

class Stock(BaseModel):
    symbol: str
    name: Optional[str] = None
    price: Optional[float] = None
    change: Optional[float] = None
    changePercent: Optional[float] = None


class StockSearchResponse(BaseModel):
    results: List[Stock]


class SyncRequest(BaseModel):
    results : List[Stock]


class QuoteResponse(BaseModel):
    results: List[Stock]


class PopularStocksResponse(BaseModel):
    results: List[Stock]


# ----------- Popular stocks endpoint -----------
@app.get("/stocks/popular", response_model=PopularStocksResponse)
def get_popular_stocks():
    # In a real app, this would fetch the most popular stocks from the database or an external API.
    # For now, we return a dummy response.
    
    stocks = [
        Stock(symbol="AAPL", name="Apple Inc.", price=150.00, change=1.50, changePercent=1.01),
        Stock(symbol="GOOGL", name="Alphabet Inc.", price=2800.00, change=-10.00, changePercent=-0.36),
        Stock(symbol="AMZN", name="Amazon.com Inc.", price=3400.00, change=20.00, changePercent=0.59),
    ]

    results = PopularStocksResponse(results=stocks)

    return results


# ----------- Search endpoint -----------

@app.get("/stocks/search", response_model=StockSearchResponse)
def search_stocks(q: str = Query(..., min_length=1)):
    
    q_lower = q.lower()
    raw = get_stocks_by_search(q_lower)

    stocks = [
        Stock(symbol=item.split(",")[0].strip("{}"), name=item.split(",")[1].strip("}"))
        for item in raw
    ]
    
    results = StockSearchResponse(results=stocks)

    return results


# ---------- Sync watchlist endpoint ----------

@app.post("/watchlist/sync")
async def sync_watchlist(request: SyncRequest):
    #print("request:", request)
    return {"ok": True}



# --------- Get stock prices ------------

@app.get("/stocks/quotes", response_model=QuoteResponse)
def get_quotes(q: str = Query(...)):
    # q = [list of Symbols]

    symbols = [item.strip() for item in q.split(",")]

    stocks = []
    for sym in symbols:

        
        stock = get_stock_by_short_name()

        if stock['price'] is not None:
            thisStock = Stock(
                symbol = sym,
                price = stock['price'],
                change = stock['price_change'],
                changePercent= stock['price_change_percent']
            )
        else:
            thisStock = Stock(
                symbol = sym
            )

        stocks.append(thisStock)

    results = QuoteResponse(results=stocks)


    return results
    


if __name__ == "__main__":
    # running on http://127.0.0.1:5000/
    uvicorn.run(app, host="127.0.0.1", port=5000)