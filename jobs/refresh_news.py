from services import get_gn_news_by_symbol
from db import insert_news, get_active_short_names


def run_refresh_news():

    success, skipped, failed = 0, 0, 0

    for stock_symbol in get_active_short_names():
        data = get_gn_news_by_symbol(stock_symbol)
        if data is not None:
            for article in data['articles']:
                result = insert_news(
                    short_name=stock_symbol,
                    source=article['source']['name'],
                    source_type='API',
                    publish_time=article['publishedAt'],
                    url=article['url'],
                    title=article['title'],
                    source_url=article['source']['url'],
                    source_country=article['source']['country'],
                    lang=article['lang'],
                    image=article['image'],
                    description=article['description'],
                    sentiment=None,
                    ai_summary=None
                )
                if result is None:
                    skipped += 1  # already exists
                else:
                    success += 1
        else:
            failed += 1

    print(f"[refresh_news] Inserted: {success} | Skipped (duplicate): {skipped} | Failed (no data): {failed}")
