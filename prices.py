import requests
import config
import json



def get_stock_price(symbol):

    base_url = "https://stockprices.dev/api/stocks/"

    try:
        response = requests.get(base_url + symbol, timeout=10)

        if response.status_code == 404:
            # Symbol not found in API → skip
            return "ERROR: Symbol not found in API"

        response.raise_for_status()  # raise for real errors (4xx/5xx)

        return dict(response.json())
    

    except requests.exceptions.RequestException as e:
        # Network error, timeout, bad response, etc.
        print(f"Error fetching {symbol}: {e}")
        return None
    

def get_stock_price_av(symbol):

    key = config.get_alpha_vantage_key()
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={key}"

    try:
        #response = requests.get(url, timeout=10)
        #response.raise_for_status()
        response = """ {
                        "Global Quote": {
                            "01. symbol": "AAPL",
                            "02. open": "258.6300",
                            "03. high": "258.7700",
                            "04. low": "254.3700",
                            "05. price": "257.4600",
                            "06. volume": "41120042",
                            "07. latest trading day": "2026-03-06",
                            "08. previous close": "260.2900",
                            "09. change": "-2.8300",
                            "10. change percent": "-1.0872%"
                        }
                    }"""

        data = json.loads(response)
        #data = response.json()

        if len(data["Global Quote"]) == 0:
            print(f"Error fetching instrument {symbol}")
            return None
        else:
            price = float(data["Global Quote"]["05. price"])
            change = float(data["Global Quote"]["09. change"])
            change_percent = float(data["Global Quote"]["10. change percent"][:-1])

            response = {"p": price, "pc": change, "pcp": change_percent}
            print(f"PRICE {symbol} ", response)

            return {"p": price, "pc": change, "pcp": change_percent}

    except requests.exceptions.RequestException as e:
        print(f"Error fetching {symbol} from Alpha Vantage: {e}")
        return None
    


    
    


 