from services.news_service import fetch_latest_news
from db import insert_news, get_active_short_names


def run_refresh_news():

    for short_name in get_active_short_names():
        for article in fetch_latest_news(short_name):
            insert_news(
                short_name=short_name,
                title=article["title"],
                publisher=article["publisher"],
                publish_time=article["publish_time"],
                web_link=article["url"],
            )