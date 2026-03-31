"""
    TODO: import and use 'accelerate'
"""

from transformers import pipeline
import torch

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


def _label(result):
    label = result["label"]
    score = result["score"]

    if label == "positive":
        return round(score, 3)
    elif label == "negative":
        return -round(score, 3)
    else:
        return 0


def get_sentiment(text: str) -> float:
    print(f"[get_sentiment] calculating sentiment for 1 article")
    result = _get_classifier()(text)[0]
    return _label(result)


def get_bulk_sentiment(texts: list[str]) -> list[float]:
    print(f"[get_bulk_sentiment] calculating sentiment for {len(texts)} articles")
    results = _get_classifier()(texts)
    return [_label(r) for r in results] 


