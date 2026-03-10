from services import get_instruments
from db import insert_stock

def run_refresh_stocks():
    instruments = get_instruments()
    if instruments is None:
        print("Skipping refresh - failed to fetch instruments")
        return

    for stock in instruments:
        insert_stock(
            shortName = stock['shortName'],
            name = stock['name'],
            type = stock['type']
        )