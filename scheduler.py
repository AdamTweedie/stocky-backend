from apscheduler.schedulers.blocking import BlockingScheduler
from jobs import run_refresh_stocks, update_stock_prices, update_free_stocks
from jobs import run_refresh_news
from jobs import run_aggregate_sentiment

scheduler = BlockingScheduler()

# refresh stock list once a week, monday at midnight
scheduler.add_job(run_refresh_stocks, "cron", day_of_week="mon", hour=0, minute=0)

# update stock prices every 15 minutes
scheduler.add_job(update_stock_prices, "interval", minutes=60)

# refresh news every hour
scheduler.add_job(run_refresh_news, "interval", hours=1)

# aggregate sentiment once a day at 11pm
scheduler.add_job(run_aggregate_sentiment, "cron", hour=23, minute=0)

if __name__ == "__main__":
    print("Starting scheduler...")
    
    # run all jobs once immediately on startup
    run_refresh_stocks()
    update_stock_prices()
    run_refresh_news()
    run_aggregate_sentiment()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped.")
        scheduler.shutdown()