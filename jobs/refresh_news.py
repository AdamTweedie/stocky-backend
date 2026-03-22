from services import get_gn_news_by_symbol, get_sentiment, fetch_rss_news
from db import insert_news, get_active_short_names


def insert_articles(articles: list[dict], stock_symbol: str, source_type: str) -> tuple[int, int]:
    """Helper to insert a list of articles and return (success, skipped) counts."""
    success, skipped = 0, 0
    for article in articles:
        sentT = get_sentiment(article['title'])
        sentD = get_sentiment(article['description']) if article['description'] else 0
        sentAvg = (sentT + sentD) / 2

        result = insert_news(
            short_name=stock_symbol,
            source=article['source']['name'],
            source_type=source_type,
            publish_time=article['publishedAt'],
            url=article['url'],
            title=article['title'],
            source_url=article['source']['url'],
            source_country=article['source']['country'],
            lang=article['lang'],
            image=article['image'],
            description=article['description'],
            sentiment=sentAvg,
            ai_summary=None
        )
        if result is None:
            skipped += 1
        else:
            success += 1
    return success, skipped


def run_refresh_news():
    success, skipped, failed = 0, 0, 0

    for stock_symbol in get_active_short_names():
        data = get_gn_news_by_symbol(stock_symbol)

        if data is not None:
            s, sk = insert_articles(data['articles'], stock_symbol, source_type='API')
            success += s
            skipped += sk
        else:
            print(f"[refresh_news] API failed for {stock_symbol}, trying RSS...")
            rss_articles = fetch_rss_news(stock_symbol)

            if rss_articles is not None:
                s, sk = insert_articles(rss_articles, stock_symbol, source_type='RSS')
                success += s
                skipped += sk
            else:
                print(f"[refresh_news] No data found for {stock_symbol} via API or RSS")
                failed += 1

    print(f"[refresh_news] ✅ Inserted: {success} | ⏭️ Skipped (duplicate): {skipped} | ❌ Failed (no data): {failed}")