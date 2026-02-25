import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from quantix_core.database.connection import db
from quantix_core.engine.signal_watcher import SignalWatcher
from twelvedata import TDClient
from quantix_core.config.settings import settings

def force_check():
    # Initialize Watcher components
    supabase = db.client
    td_client = TDClient(apikey=settings.TWELVE_DATA_API_KEY)
    
    watcher = SignalWatcher(
        supabase_client=supabase,
        td_client=td_client,
        check_interval=60
    )
    
    sig_id = 'a667de47-721c-40a1-990b-84642cc5dc0e'
    print(f"Force checking signal: {sig_id}")
    
    # 1. Get signal from DB
    res = supabase.table("fx_signals").select("*").eq("id", sig_id).execute()
    if not res.data:
        print("Signal not found.")
        return
    signal = res.data[0]
    
    # 2. Get latest price (Binance fallback)
    import requests
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=EURUSDT")
        price = float(r.json()["price"])
        print(f"Current Price (Binance): {price}")
        
        # Mock a candle object for the watcher
        candle = {
            "close": price,
            "high": price, # Conservative
            "low": price,
            "timestamp": "now"
        }
        
        # Run check
        print(f"Running watcher logic... Current state: {signal['state']}")
        watcher.check_signal(signal, candle)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_check()
