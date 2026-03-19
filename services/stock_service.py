import requests
from config import get_212_pk, get_212_sk, get_212_auth_header, get_instruments_url
import config
import json


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
                "shortName": item["shortName"],
                "name": item["name"],
                "type": item["type"]
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
    

def get_stock_price_av(symbol):
    key = config.get_alpha_vantage_key()
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # handle missing key or rate limit response
        if "Note" in data or "Information" in data:
            return "FREE_TIER_RATE_BLOCK"
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
    