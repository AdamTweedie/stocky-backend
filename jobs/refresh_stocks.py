from services import get_instruments, get_stock_price_av, get_stock_price_spd, get_stock_price_yf
from db import (
    insert_stock, 
    update_stock, 
    reset_free_tier, 
    get_active_short_names,
    bulk_update_stock_prices,
    bulk_insert_stocks,
    get_stock_by_short_name,
    get_quote_by_symbol
)
import time
from mappings import is_market_open, currency_exchange_suffix


def fetch_price_with_fallback(short_name: str, currency_code: str, long_name: str = None, type: str = "STOCK") -> dict | None:
    
    print(f"[fetch_price_with_fallback] {short_name}")

    # 1. try Alpha Vantage
    av_not_none = True
    delay = 0
    if delay > 0:
        time.sleep(delay)
    while av_not_none:
        price_dict = get_stock_price_av(symbol=short_name, currency_code=currency_code)
        if price_dict == "REDUCE_RATE_TO_1_PER_SECOND":
            delay = 1
        elif price_dict is not None:
            return price_dict
        else:
            av_not_none = False
            print(f"[fetch_price_with_fallback] AV rate limited, trying yfinance...")

    # 2. try yfinance
    print(f"[fetch_price_with_fallback] AV failed for {short_name}, trying yfinance...")
    price_dict = get_stock_price_yf(symbol=short_name, name=long_name, currency_code=currency_code)
    if price_dict is not None:
        return price_dict

    # 3. try stockprices.dev
    print(f"[fetch_price_with_fallback] yfinance failed for {short_name}, trying stockprices.dev...")
    price_dict = get_stock_price_spd(symbol=short_name, currency_code=currency_code, type=type)
    if price_dict is not None:
        return price_dict

    print(f"[fetch_price_with_fallback] All sources failed for {short_name}")
    return None


def run_refresh_stocks():
    """
    Updates stocks with new instruments if new instruments exist in get_instruments()
    """
    instruments = get_instruments()
    if instruments is None:
        print("Skipping refresh - failed to fetch instruments")
        return

    count = bulk_insert_stocks(instruments)
    print(f"[run_refresh_stocks] {count} new stocks inserted")


def update_free_stocks(short_names: list[str]) -> dict:
    """
    Sets in_free_tier = True for given short_names, and resets all others to False.
    Returns a summary of the operation.
    """
    reset_free_tier()

    success, failed = [], []
    for short_name in short_names:
        result = update_stock(short_name, in_free_tier=True)
        if result:
            success.append(short_name)
        else:
            failed.append(short_name)

    print(f"[update_free_stocks] {len(success)} updated, {len(failed)} not found: {failed}")
    return {"success": success, "failed": failed}


def update_stock_prices() -> dict:
    """
    Updates the stock prices of the active symbols
    """
    updates, failed = [], []
    delay = 0

    active = get_active_short_names()
    print(f"[update_stock_prices] Updating {len(active)} symbols...")

    for _, short_name in enumerate(active):
        if delay > 0:
            time.sleep(delay)

        stock = get_stock_by_short_name(short_name)
        if not is_market_open(stock["currency_code"]):
            print(f"[update_stock_prices] Market closed for {short_name}, skipping")
            continue

        price_dict = fetch_price_with_fallback(short_name, stock["currency_code"], stock["name"], stock["type"])

        if price_dict is None:
            failed.append(short_name)
        else:
            updates.append({
                "short_name":          short_name,
                "price":               price_dict["p"],
                "price_change":        price_dict["pc"],
                "price_change_percent": price_dict["pcp"]
            })

    updated = bulk_update_stock_prices(updates)
    print(f"[update_stock_prices] {updated} updated, {len(failed)} failed: {failed}")
    return {"success": [u["short_name"] for u in updates], "failed": failed}


def update_single_stock_price(short_name: str) -> dict:
    """
    Fetches and updates the price of a single stock symbol on demand.
    Tries AV, then yfinance, then stockprices.dev.
    """
    stock = get_stock_by_short_name(short_name)
    if not stock:
        print(f"[update_single_stock_price] Stock {short_name} not found in db")
        return {"success": False, "short_name": short_name, "price": None, "price_change": None, "price_change_percent": None}

    price_dict = fetch_price_with_fallback(short_name, stock["currency_code"], stock["name"], stock["type"])

    if price_dict is None:
        print(f"[update_single_stock_price] All sources failed for {short_name}")
        return {"success": False, "short_name": short_name, "price": None, "price_change": None, "price_change_percent": None}

    update_stock(
        short_name,
        price=price_dict["p"],
        price_change=price_dict["pc"],
        price_change_percent=price_dict["pcp"]
    )

    print(f"[update_single_stock_price] ✅ {short_name} → {price_dict['p']} ({price_dict['pcp']}%)")
    return {
        "success":              True,
        "short_name":           short_name,
        "price":                price_dict["p"],
        "price_change":         price_dict["pc"],
        "price_change_percent": price_dict["pcp"],
        "currency_code":        stock["currency_code"]
    }


def get_or_fetch_quote(sym: str) -> dict | None:
    item = get_quote_by_symbol(sym)
    print(f"[get_or_fetch_quote] DB lookup for {sym}: {item}")

    if item is None:
        return None

    if item["price"] is not None:
        return item

    print(f"[get_or_fetch_quote] Price missing for {sym}, fetching...")
    result = update_single_stock_price(sym)
    print(f"[get_or_fetch_quote] result: {result}")

    if result["success"]:
        return {
            "short_name":           sym,
            "price":                result["price"],
            "price_change":         result["price_change"],
            "price_change_percent": result["price_change_percent"],
            "currency_code":        item["currency_code"]
        }

    return None
