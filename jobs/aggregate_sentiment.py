from db import aggregate_daily_sentiment

def run_aggregate_sentiment():
    count = aggregate_daily_sentiment()
    print(f"[aggregate_sentiment] ✅ Aggregated sentiment for {count} stocks")