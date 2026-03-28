import requests
from config import get_212_pk, get_212_sk, get_212_auth_header, get_instruments_url
import config
import json
import yfinance as yf
from mappings import currency_exchange_suffix


INSTRUMENT_URL = get_instruments_url()
AUTH_HEADER = get_212_auth_header()
PK = get_212_pk()
SK = get_212_sk()


def get_instruments() -> list[dict] | None:
    """
    Fetches the list of instruments from Trading212 API.
    Returns a list of stocks, or None if the request fails.
    """

    headers = {"Authorization": AUTH_HEADER}

    try:
        response = requests.get(
            INSTRUMENT_URL,
            headers=headers,
            auth=(PK, SK)
        )
    
        response.raise_for_status()
        data = response.json()

        ALLOWED_TYPES = {"STOCK", "ETF"}
        
        stocks = [
            {
                "ticker": item["ticker"],
                "shortName": item["shortName"],
                "name": item["name"],
                "type": item["type"],
                "currencyCode": item["currencyCode"]
            }
            for item in data if item["type"] in ALLOWED_TYPES
        ]

        return stocks

    except requests.exceptions.HTTPError as e:
        print(f"[get_instruments] HTTP error: {e.response.status_code}")
        return None
    except requests.exceptions.ConnectionError:
        print("[get_instruments] Connection error — could not reach API")
        return None
    except requests.exceptions.Timeout:
        print("[get_instruments] Request timed out")
        return None
    except Exception as e:
        print(f"[get_instruments] Unexpected error: {e}")
        return None
    

def is_rate_limited(data):
    if "Information" not in data:
        return False
    if "1 request per second" in data["Information"]:
        return True


def _build_ticker(short_name: str, currency_code: str) -> str:
    """
    Build a yfinance compatible ticker from Trading212 data.
    Uses currency code to determine the correct exchange suffix.
    """

    suffix = currency_exchange_suffix(currency_code)
    return f"{short_name}{suffix}"


def get_stock_price_av(symbol: str, currency_code: str) -> dict | None:
    symbol = _build_ticker(symbol, currency_code)
    key = config.get_alpha_vantage_key()
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # handle missing key or rate limit response
        if is_rate_limited(data):
            print(f"[get_stock_price_av] Alpha Vantage free tier detected - reduce API call to 1 per second")
            return "REDUCE_RATE_TO_1_PER_SECOND"
        if "Global Quote" not in data:
            print(f"[get_stock_price_av] Unexpected response for {symbol}: {data}")
            return None

        if len(data["Global Quote"]) == 0:
            print(f"[get_stock_price_av] Empty quote for {symbol}")
            return None

        price = float(data["Global Quote"]["05. price"])
        change = float(data["Global Quote"]["09. change"])
        change_percent = float(data["Global Quote"]["10. change percent"][:-1])

        return {"p": price, "pc": change, "pcp": change_percent}

    except requests.exceptions.RequestException as e:
        print(f"[get_stock_price_av] Error fetching {symbol}: {e}")
        return None
    

def get_stock_price_spd(symbol: str, currency_code: str, type: str = "STOCK") -> dict | None:
    """
    Fetch stock price from stockprices.dev — free, no API key required.
    type: "STOCK" or "ETF"
    """
    symbol = _build_ticker(symbol, currency_code)

    try:
        endpoint = "etfs" if type == "ETF" else "stocks"
        response = requests.get(
            f"https://stockprices.dev/api/{endpoint}/{symbol}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        if not data:
            print(f"[get_stock_price_spd] Empty response for {symbol}")
            return None

        return {
            "p":   data["Price"],
            "pc":  data["ChangeAmount"],
            "pcp": data["ChangePercentage"]
        }

    except requests.exceptions.RequestException as e:
        print(f"[get_stock_price_spd] Error fetching {symbol}: {e}")
        return None


def get_stock_price_yf(symbol: str, name: str, currency_code: str = None, type: str = "STOCK") -> dict | None:
    """
    Search for a stock price using yfinance search — no exact ticker needed.
    Falls back through multiple search strategies.
    """
    # strategy 1: try short_name directly
    # strategy 2: try short_name + exchange suffix from currency
    # strategy 3: search by company name

    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info.last_price
        if price and price > 0:
            prev_close = ticker.fast_info.previous_close
            change = price - prev_close
            change_pct = (change / prev_close) * 100
            print(f"[get_stock_price_by_name] ✅ {symbol} resolved via {symbol}")
            return {"p": price, "pc": change, "pcp": change_pct}
    except Exception as e:
        print(f"[get_stock_price_by_name] failed with exception {e}, will search for valid symbols...")

    try:
        results = yf.Search(symbol).all
        if results and "quotes" in results:
            quotes = results.get("quotes")[:3]
            for quote in quotes:
                ticker = yf.Ticker(quote["symbol"])
                price = ticker.fast_info.last_price
                if price and price > 0:
                    prev_close = ticker.fast_info.previous_close
                    change = price - prev_close
                    change_pct = round((change / prev_close) * 100, 3)
                    print(f"[get_stock_price_by_name] ✅ {symbol} resolved via search → {quote['symbol']}")
                    return {"p": price, "pc": change, "pcp": change_pct}
    except Exception as e:
        print(f"[get_stock_price_by_name] Search failed for {symbol}: {e}")

    print(f"[get_stock_price_by_name] ❌ All strategies failed for {symbol}")
    return None