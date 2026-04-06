from services import summarise_article
from db import update_news_by_id


def update_ai_summary(news_id: int, stock_short_name: str, news_url: str, news_title: str, news_description: str):

    response = summarise_article(news_id, stock_short_name, news_url, news_title, news_description)
    if response is None:
        print(f"[update_ai_summary] summarise_article returned None for news_id {news_id}")
        return None
    
    try:
        news_id = response["news_id"]
        ai_summary = response["summary"]
        tokens_in = ["tokens_in"]
        tokens_out = ["tokens_out"]

        # update the news row in the db
        update_news_by_id(news_id=news_id, AI_summary=ai_summary)

        return {"id": news_id, "ai_summary": ai_summary, "tokens_in": tokens_in, "tokens_out": tokens_out}

        #TODO: update user token usage

    
    except Exception as e:
        print(f"[update_ai_summary] error updating AI summary for {news_id}: {e}")
        return None