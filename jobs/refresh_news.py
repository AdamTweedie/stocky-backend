from services import get_gn_news_by_symbol, get_bulk_sentiment, fetch_rss_news
from db import (insert_news, 
                get_active_short_names, 
                get_news_by_title, 
                get_title_and_descriptions_from_ids,
                bulk_update_sentiment_by_id,)


def insert_articles(articles: list[dict],
                    stock_symbol: str,
                    source_type: str) -> tuple[int, int]:
    """Helper to insert a list of articles and return (success, skipped) counts."""
    success, skipped = 0, 0
    titles = []
    for article in articles:
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
            sentiment=None,
            ai_summary=None
        )
        if result is None:
            skipped += 1
        else:
            success += 1
            titles.append(article["title"])

    article_ids = []
    for title in titles:
        article_ids.append(get_news_by_title(title)["id"])
    
    return success, skipped, article_ids


def run_refresh_news():
    success, skipped, failed = 0, 0, 0
    article_ids = []
    for stock_symbol in get_active_short_names():
        data = get_gn_news_by_symbol(stock_symbol)

        if data is not None:
            s, sk, ids = insert_articles(data['articles'], stock_symbol, source_type='API')
            success += s
            skipped += sk
            article_ids += ids
        else:
            print(f"[refresh_news] API failed for {stock_symbol}, trying RSS...")
            rss_articles = fetch_rss_news(stock_symbol)

            if rss_articles is not None:
                s, sk, ids = insert_articles(rss_articles, stock_symbol, source_type='RSS')
                success += s
                skipped += sk
                article_ids += ids
            else:
                print(f"[refresh_news] No data found for {stock_symbol} via API or RSS")
                failed += 1

    
    
    if len(article_ids) > 0:
        scores, texts = [], []
        results = get_title_and_descriptions_from_ids(article_ids)
        
        texts = [
            f"{r['title']}. {r['description']}" if r['description']
            else r['title']
            for r in results
        ]
        
        scores = get_bulk_sentiment(texts=texts)

        article_scores = {id: score for id, score in zip(results, scores)}

        sents = bulk_update_sentiment_by_id(article_scores=article_scores)


    print(f"[refresh_news] ✅ Inserted: {success} | ⏭️ Skipped (duplicate): {skipped} | ❌ Failed (no data): {failed}")
    if sents is not None:
        print(f"[refresh_news] Inserted sentiment for {sents}/{success+skipped+failed} articles!")


