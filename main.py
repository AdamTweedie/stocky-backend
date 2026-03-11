import jobs
import db



if __name__ == "__main__":

    jobs.update_stock_prices()

    active = db.get_active_short_names()

    stocks = []
    for astock in active:
        stock = db.get_stock_by_short_name(astock)
        stocks.append(stock)

    for stock in stocks:
        print(stock)
    