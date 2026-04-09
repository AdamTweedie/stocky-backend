from pydoc import html
from config import gnews_key, trusted_rss_feeds
from db import get_active_short_names, insert_news, get_stock_by_short_name
from bs4 import BeautifulSoup
import requests
import json
import feedparser
from datetime import datetime, timezone
import re
from urllib.parse import urljoin
from typing import Optional, Tuple
import time


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


def _try_resolve_url_and_image(rss_url: str) -> Tuple[str | None, str | None]:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(rss_url, headers=headers, allow_redirects=True, timeout=10)
        response.raise_for_status()

        final_url = response.url
        html = response.text

        # Retry fetch if needed (Google News edge case)
        if "og:image" not in html:
            html = requests.get(final_url, headers=headers, timeout=10).text

        soup = BeautifulSoup(html, "html.parser")

        # --- Meta images ---
        for attr in [
            ("property", "og:image"),
            ("property", "og:image:secure_url"),
            ("name", "twitter:image"),
        ]:
            tag = soup.find("meta", attrs={attr[0]: attr[1]})
            if tag and tag.get("content"):
                return final_url, tag.get("content")

        # --- Fallback images ---
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src and not src.endswith(".svg"):
                return final_url, urljoin(final_url, src)

        return final_url, None

    except Exception as e:
        print(f"[try_resolve_url_and_image] Error: {e}")
        return None, None


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
    seen_urls = set()

    for source_domain, urls in feeds.items():
        for url in urls:
            try:
                feed = feedparser.parse(url)

                if feed.bozo:
                    print(f"[fetch_rss_news] Malformed feed: {source_domain}")
                    continue

                for entry in feed.entries:
                    title = entry.get("title", "")
                    url = entry.get("link")
                    title_lower = title.lower()
                    description = entry.get("summary", "").lower()
                    combined = title_lower + " " + description
                    image_url = None

                    if not article_matches_stock(combined, symbol, name_keywords):
                        continue

                    if title_lower in seen_titles or url in seen_urls:
                        continue

                    seen_titles.add(title_lower)
                    seen_urls.add(url)

                    source_url, source_image_url = _try_resolve_url_and_image(url) 

                    if source_url is not None:
                        url = source_url
                    if source_image_url is not None:
                        image_url = source_image_url

                    articles.append({
                        "title":       title,
                        "url":         url,
                        "publishedAt": _parse_rss_date(entry.get("published")),
                        "description": None,
                        "image":       image_url,
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

        time.sleep(0.25)  # be polite to servers

    if not articles:
        print(f"[fetch_rss_news] No articles found for {short_name} / {name_keywords}")
        return None

    print(f"[fetch_rss_news] Found {len(articles)} articles for {short_name} / {name_keywords}")
    return articles