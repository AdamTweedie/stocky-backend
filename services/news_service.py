from config import gnews_key
from db import get_active_short_names, insert_news
import requests
import json


# --- GNEWS GET ---
def get_gn_news_by_symbol(name: str, lang: str = 'en', max: int = 5) -> list[dict] | None:

    GNEWS_KEY = gnews_key()
    url = f"https://gnews.io/api/v4/search?q={name}&lang={lang}&max={max}&apikey={GNEWS_KEY}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data

    except requests.exceptions.RequestException as e:
        
        return None
    



    




