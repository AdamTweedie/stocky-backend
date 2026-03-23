from config import get_deepseek_key
from db import update_news_by_id, get_news_by_short_name, get_news_by_id
from datetime import datetime, timezone, timedelta
from openai import OpenAI


client = OpenAI(
    api_key=get_deepseek_key(),
    base_url="https://api.deepseek.com",
)


SUMMARY_SYSTEM_PROMPT = """You are a concise financial news analyst. 
When given a news article title, description, and URL, provide a clear and objective summary in exactly 2 paragraphs.
Focus on the key facts, market implications, and what it means for the stock. 
Do not include any disclaimers or investment advice."""


def summarise_article(
        news_id: int,
        short_name: str,
        url: str,
        title: str,
        description: str,
    ) -> dict | None:

    """
    Generate an AI summary for a single news article.
    Updates the news row in the db with the summary.
    Returns summary text and token usage, or None if it fails.
    """
    if get_news_by_id(news_id)["AI_summary"] is not None:
        print(f"[summarise_article] AI_summary already exists for news id {news_id}")
        return None
    if not title or not description:
        print(f"[summarise_article] No title or description provided for news_id {news_id}")
        return None
    elif not url:
        print(f"[summarise_article] No URL provided for news_id {news_id}")
        return None
    
    user_prompt = f"""
    Stock: {short_name}
    Title: {title}
    Description: {description or 'No description available'}
    url: {url}
    Please summarise this news article in 2 paragraphs."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=300,  # roughly 2 paragraphs
        )

        summary = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        # update the news row in the db
        update_news_by_id(news_id, ai_summary=summary)

        print(f"[summarise_article] {short_name} | news_id {news_id} | tokens in: {tokens_in} out: {tokens_out}")

        return {
            "news_id":    news_id,
            "summary":    summary,
            "tokens_in":  tokens_in,
            "tokens_out": tokens_out,
        }

    except Exception as e:
        print(f"[summarise_article] Error for news_id {news_id}: {e}")
        return None


def summarise_recent_news(short_name: str, days: int = 3) -> dict | None:
    """
    Generate a combined AI summary of all news for a stock over the last N days.
    This is a premium feature — check tier before calling.
    Returns the summary and total token usage.
    """
    articles = get_news_by_short_name(short_name, limit=50)

    # filter to last N days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [
        a for a in articles
        if a["publish_time"] and a["publish_time"] >= cutoff.isoformat()
    ]

    if not recent:
        print(f"[summarise_recent_news] No recent articles found for {short_name}")
        return None

    # build a digest of all recent headlines and descriptions
    digest = "\n\n".join([
        f"- {a['title']}: {a['description'] or 'No description'}"
        for a in recent
    ])

    user_prompt = f"""Stock: {short_name}
    Here are the last {days} days of news articles:

    {digest}

    Please provide a 4 paragraph summary of the overall news sentiment and key themes for {short_name} over this period."""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=400,
        )

        summary = response.choices[0].message.content.strip()
        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        print(f"[summarise_recent_news] {short_name} | {len(recent)} articles | tokens in: {tokens_in} out: {tokens_out}")

        return {
            "short_name":     short_name,
            "articles_used":  len(recent),
            "summary":        summary,
            "tokens_in":      tokens_in,
            "tokens_out":     tokens_out,
        }

    except Exception as e:
        print(f"[summarise_recent_news] Error for {short_name}: {e}")
        return None