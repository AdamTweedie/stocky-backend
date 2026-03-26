import pytz 
from datetime import datetime

CURRENCY_EXCHANGE_SUFFIX = {
    "USD": "",       # US stocks need no suffix
    "GBP": ".L",     # London Stock Exchange
    "GBX": ".L",     # London Stock Exchange (pence)
    "EUR": ".AS",    # default EUR to Euronext Amsterdam
    "CHF": ".SW",    # Swiss Exchange
    "SEK": ".ST",    # Stockholm
    "NOK": ".OL",    # Oslo
    "DKK": ".CO",    # Copenhagen
    "CAD": ".TO",    # Toronto
}


def currency_exchange_suffix(curr: str) -> str:
    return CURRENCY_EXCHANGE_SUFFIX.get(curr, "")


CURRENCY_EXCHANGE_HOURS = {
    # North America
    "USD": {
        "exchange": "NYSE/NASDAQ",
        "timezone": "America/New_York",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "CAD": {
        "exchange": "TSX",
        "timezone": "America/Toronto",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "MXN": {
        "exchange": "BMV",
        "timezone": "America/Mexico_City",
        "open":  {"hour": 8,  "minute": 30},
        "close": {"hour": 15, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },

    # UK
    "GBP": {
        "exchange": "LSE",
        "timezone": "Europe/London",
        "open":  {"hour": 8,  "minute": 0},
        "close": {"hour": 16, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "GBX": {  # pence-denominated LSE stocks
        "exchange": "LSE",
        "timezone": "Europe/London",
        "open":  {"hour": 8,  "minute": 0},
        "close": {"hour": 16, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },

    # Europe
    "EUR": {
        "exchange": "Euronext/XETRA",
        "timezone": "Europe/Paris",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "CHF": {
        "exchange": "SIX Swiss Exchange",
        "timezone": "Europe/Zurich",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "SEK": {
        "exchange": "Nasdaq Stockholm",
        "timezone": "Europe/Stockholm",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "NOK": {
        "exchange": "Oslo Stock Exchange",
        "timezone": "Europe/Oslo",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 16, "minute": 20},
        "days": [0, 1, 2, 3, 4]
    },
    "DKK": {
        "exchange": "Nasdaq Copenhagen",
        "timezone": "Europe/Copenhagen",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "PLN": {
        "exchange": "Warsaw Stock Exchange",
        "timezone": "Europe/Warsaw",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 5},
        "days": [0, 1, 2, 3, 4]
    },
    "CZK": {
        "exchange": "Prague Stock Exchange",
        "timezone": "Europe/Prague",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "HUF": {
        "exchange": "Budapest Stock Exchange",
        "timezone": "Europe/Budapest",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },

    # Asia Pacific
    "JPY": {
        "exchange": "Tokyo Stock Exchange",
        "timezone": "Asia/Tokyo",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 15, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "HKD": {
        "exchange": "Hong Kong Stock Exchange",
        "timezone": "Asia/Hong_Kong",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "CNY": {
        "exchange": "Shanghai/Shenzhen Stock Exchange",
        "timezone": "Asia/Shanghai",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 15, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "CNH": {  # offshore Chinese yuan, same hours as CNY
        "exchange": "Shanghai/Shenzhen Stock Exchange",
        "timezone": "Asia/Shanghai",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 15, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "KRW": {
        "exchange": "Korea Stock Exchange",
        "timezone": "Asia/Seoul",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 15, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "INR": {
        "exchange": "BSE/NSE",
        "timezone": "Asia/Kolkata",
        "open":  {"hour": 9,  "minute": 15},
        "close": {"hour": 15, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "SGD": {
        "exchange": "Singapore Exchange",
        "timezone": "Asia/Singapore",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "AUD": {
        "exchange": "Australian Securities Exchange",
        "timezone": "Australia/Sydney",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "NZD": {
        "exchange": "New Zealand Stock Exchange",
        "timezone": "Pacific/Auckland",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "TWD": {
        "exchange": "Taiwan Stock Exchange",
        "timezone": "Asia/Taipei",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 13, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "MYR": {
        "exchange": "Bursa Malaysia",
        "timezone": "Asia/Kuala_Lumpur",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "THB": {
        "exchange": "Stock Exchange of Thailand",
        "timezone": "Asia/Bangkok",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 16, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },
    "IDR": {
        "exchange": "Indonesia Stock Exchange",
        "timezone": "Asia/Jakarta",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 15, "minute": 49},
        "days": [0, 1, 2, 3, 4]
    },
    "PHP": {
        "exchange": "Philippine Stock Exchange",
        "timezone": "Asia/Manila",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 15, "minute": 30},
        "days": [0, 1, 2, 3, 4]
    },

    # Middle East & Africa
    "ILS": {
        "exchange": "Tel Aviv Stock Exchange",
        "timezone": "Asia/Jerusalem",
        "open":  {"hour": 9,  "minute": 59},
        "close": {"hour": 17, "minute": 25},
        "days": [0, 1, 2, 3, 6]  # Sunday to Thursday
    },
    "AED": {
        "exchange": "Dubai Financial Market",
        "timezone": "Asia/Dubai",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 14, "minute": 0},
        "days": [0, 1, 2, 3, 6]  # Sunday to Thursday
    },
    "SAR": {
        "exchange": "Tadawul",
        "timezone": "Asia/Riyadh",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 15, "minute": 0},
        "days": [0, 1, 2, 3, 6]  # Sunday to Thursday
    },
    "ZAR": {
        "exchange": "Johannesburg Stock Exchange",
        "timezone": "Africa/Johannesburg",
        "open":  {"hour": 9,  "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "EGP": {
        "exchange": "Egyptian Exchange",
        "timezone": "Africa/Cairo",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 14, "minute": 30},
        "days": [0, 1, 2, 3, 6]  # Sunday to Thursday
    },

    # South America
    "BRL": {
        "exchange": "B3 Brazil",
        "timezone": "America/Sao_Paulo",
        "open":  {"hour": 10, "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "ARS": {
        "exchange": "Buenos Aires Stock Exchange",
        "timezone": "America/Argentina/Buenos_Aires",
        "open":  {"hour": 11, "minute": 0},
        "close": {"hour": 17, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "CLP": {
        "exchange": "Santiago Stock Exchange",
        "timezone": "America/Santiago",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
    "COP": {
        "exchange": "Colombia Stock Exchange",
        "timezone": "America/Bogota",
        "open":  {"hour": 9,  "minute": 30},
        "close": {"hour": 16, "minute": 0},
        "days": [0, 1, 2, 3, 4]
    },
}


def is_market_open(currency_code: str) -> bool:
    """
    Returns True if the market for the given currency is currently open.

    Usage:
        is_market_open("USD")  -> True/False
    """
    exchange = CURRENCY_EXCHANGE_HOURS.get(currency_code)
    if not exchange:
        print(f"[is_market_open] Unknown currency code: {currency_code}, defaulting to closed")
        return False

    tz = pytz.timezone(exchange["timezone"])
    now = datetime.now(tz)

    if now.weekday() not in exchange["days"]:
        return False

    open_time  = now.replace(hour=exchange["open"]["hour"],  minute=exchange["open"]["minute"],  second=0, microsecond=0)
    close_time = now.replace(hour=exchange["close"]["hour"], minute=exchange["close"]["minute"], second=0, microsecond=0)

    return open_time <= now <= close_time