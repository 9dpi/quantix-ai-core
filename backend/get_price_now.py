
from quantix_core.feeds.binance_feed import BinanceFeed
import json

def get_current():
    feed = BinanceFeed()
    price_data = feed.get_price("EURUSD")
    print(json.dumps(price_data, indent=2))

if __name__ == "__main__":
    get_current()
