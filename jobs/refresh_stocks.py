from services import get_instruments, get_stock_price_av
from db import (
    insert_stock, 
    update_stock, 
    reset_free_tier, 
    get_active_short_names,
    bulk_update_stock_prices,
    bulk_insert_stocks
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


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
    # first reset all stocks to not free
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

    for i, short_name in enumerate(active):
        if delay > 0: 
            time.sleep(delay)
        
        price_dict = get_stock_price_av(symbol=short_name)

        if price_dict == "REDUCE_RATE_TO_1_PER_SECOND":
            print("[update_stock_prices] Free tier detected, switching to 1 request/sec")
            delay = 1
            time.sleep(delay)
            price_dict = get_stock_price_av(symbol=short_name)
        

        if price_dict is None:
            failed.append(short_name)
        else:
            updates.append({
                "short_name": short_name,
                "price": price_dict["p"],
                "price_change": price_dict["pc"],
                "price_change_percent": price_dict["pcp"]
            })

    updated = bulk_update_stock_prices(updates)

    print(f"[update_stock_prices] {updated} updated, {len(failed)} not found: {failed}")
    return {"success": [u["short_name"] for u in updates], "failed": failed}
            
            

        

