from transformers import pipeline
import torch
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

VADER_FALLBACK_THRESHOLD = 0.5

_classifier = None

def _get_classifier():
    global _classifier
    if _classifier is None:
        print("[sentiment] Loading FinBERT model...")
        device = 0 if torch.cuda.is_available() else -1
        _classifier = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            truncation=True,
            max_length=512,
            batch_size=16,
            device=device
        )
        print("[sentiment_service] ProsusAI/finbert model loaded")
    return _classifier


_vader = SentimentIntensityAnalyzer()
def get_vader_sentiment_compound_score(text: str) -> float:
    sentiment_dict = _vader.polarity_scores(text)
    return sentiment_dict["compound"]


def _label(result, text):
    label = result["label"]
    score = result["score"]

    if label == "positive":
        return round(score, 3)
    elif label == "negative":
        return -round(score, 3)
    else:
        vader_score = get_vader_sentiment_compound_score(text)
        return vader_score if abs(vader_score) > VADER_FALLBACK_THRESHOLD else 0


def get_sentiment(text: str) -> float:
    print(f"[get_sentiment] calculating sentiment for 1 article")
    result = _get_classifier()(text)[0]
    return _label(result, text)


def get_bulk_sentiment(texts: list[str]) -> list[float]:
    print(f"[get_bulk_sentiment] calculating sentiment for {len(texts)} articles")
    results = _get_classifier()(texts)
    return [_label(r, texts[i]) for i, r in enumerate(results)] 


