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

    active = get_active_short_names()
    print(f"[update_stock_prices] Updating {len(active)} symbols...")

    def fetch(short_name):
        price_dict = get_stock_price_av(symbol=short_name)
        if price_dict is None:
            return short_name, None
        return short_name, price_dict
    

    # TODO: if using alpha v free tier, drop workers to 1, and sleep 1 second between call
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch, s): s for s in active}
        for future in as_completed(futures):
            short_name, price_dict = future.result()
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
            
            

        

