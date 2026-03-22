from config import gnews_key, trusted_rss_feeds
from db import get_active_short_names, insert_news, get_stock_by_short_name
import requests
import json
import feedparser
from datetime import datetime, timezone
import re


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


# ---- RSS funky alternative ----
# common suffixes to strip from company names
STRIP_WORDS = {
    "inc", "inc.", "corp", "corp.", "ltd", "ltd.", "llc", "plc", "co", "co.",
    "company", "group", "holdings", "holding", "technologies", "technology",
    "international", "global", "services", "solutions", "enterprises",
    "industries", "industry", "partners", "capital", "financial", "bank",
    "trust", "fund", "the", "and", "&"
}


def _parse_rss_date(date_str: str) -> str | None:
    """Convert RSS date string to ISO 8601."""
    if not date_str:
        return None
    try:
        parsed = feedparser._parse_date(date_str)
        if parsed:
            dt = datetime(*parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    return date_str


def extract_name_keywords(name: str) -> list[str]:
    """
    Extract meaningful keywords from a company name by stripping generic suffixes.
    
    Examples:
        "Apple Inc."           -> ["apple"]
        "Eldorado Gold Corp"   -> ["eldorado", "gold"]
        "JPMorgan Chase & Co"  -> ["jpmorgan", "chase"]
        "Bank of America Corp" -> ["bank", "america"]
    """
    words = name.lower().replace(".", "").replace(",", "").split()
    keywords = [w for w in words if w not in STRIP_WORDS]
    return keywords if keywords else [words[0]]  # fallback to first word


def article_matches_stock(combined: str, symbol: str, name_keywords: list[str]) -> bool:
    """
    Returns True if the article mentions the symbol OR all name keywords.
    Uses whole word matching to avoid false positives like 'apples' matching 'appl'.
    """
    def whole_word_match(word: str, text: str) -> bool:
        return bool(re.search(rf'\b{re.escape(word)}\b', text))

    if whole_word_match(symbol, combined):
        return True

    if all(whole_word_match(keyword, combined) for keyword in name_keywords):
        return True

    return False


# ---- Main ting ----
def fetch_rss_news(short_name: str) -> list[dict] | None:
    stock = get_stock_by_short_name(short_name)
    if stock is None:
        print(f"[fetch_rss_news] Stock {short_name} not found in db")
        return None

    symbol = short_name.lower()
    name_keywords = extract_name_keywords(stock["name"])
    print(f"[fetch_rss_news] Searching for '{short_name}' with keywords: {name_keywords}")

    feeds = trusted_rss_feeds()
    articles = []
    seen_titles = set()

    for source_domain, urls in feeds.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)

                if feed.bozo:
                    print(f"[fetch_rss_news] Malformed feed: {source_domain}")
                    continue

                for entry in feed.entries:
                    title = entry.get("title", "")
                    title_lower = title.lower()
                    description = entry.get("summary", "").lower()
                    combined = title_lower + " " + description

                    if not article_matches_stock(combined, symbol, name_keywords):
                        continue

                    if title_lower in seen_titles:
                        continue

                    seen_titles.add(title_lower)
                    articles.append({
                        "title":       title,
                        "url":         entry.get("link"),
                        "publishedAt": _parse_rss_date(entry.get("published")),
                        "description": None,
                        "image":       None,
                        "lang":        "en",
                        "source": {
                            "name":    source_domain,
                            "url":     f"https://{source_domain}",
                            "country": "US",
                        }
                    })

            except Exception as e:
                print(f"[fetch_rss_news] Error fetching {source_domain}: {e}")
                continue

    if not articles:
        print(f"[fetch_rss_news] No articles found for {short_name} / {name_keywords}")
        return None

    print(f"[fetch_rss_news] Found {len(articles)} articles for {short_name} / {name_keywords}")
    return articles