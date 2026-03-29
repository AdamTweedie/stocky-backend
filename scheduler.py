from apscheduler.schedulers.blocking import BlockingScheduler
from jobs import run_refresh_stocks, update_stock_prices, update_free_stocks
from jobs import run_refresh_news
from jobs import run_aggregate_sentiment

scheduler = BlockingScheduler()

# refresh stock list once p/w
scheduler.add_job(run_refresh_stocks, "cron", day_of_week="mon", hour=0, minute=0)

# update stock prices 15/m
scheduler.add_job(update_stock_prices, "interval", minutes=60)

# refresh news 1p/h
scheduler.add_job(run_refresh_news, "interval", hours=1)

# aggregate 11pm 1p/d
scheduler.add_job(run_aggregate_sentiment, "cron", hour=23, minute=0)

if __name__ == "__main__":
    print("Starting scheduler...")
    
    run_refresh_stocks()
    update_stock_prices()
    run_refresh_news()
    run_aggregate_sentiment()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        scheduler.shutdown()