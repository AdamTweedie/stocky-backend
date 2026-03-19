from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyser = SentimentIntensityAnalyzer()

def get_sentiment(text: str) -> float:
    scores = analyser.polarity_scores(text)
    if scores['compound'] is None:
        return 0
    else:
        return scores['compound'] # returns -1.0 (negative) to 1.0 (positive)
