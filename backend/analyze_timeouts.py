from quantix_core.database.connection import db
from quantix_core.feeds.binance_feed import BinanceFeed
from datetime import datetime, timezone, timedelta
import pandas as pd

def analyze_timeout_signals():
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    res = db.client.table("fx_signals").select("*").eq("status", "CLOSED_TIMEOUT").gte("generated_at", today.isoformat()).execute()
    
    if not res.data:
        print("No timeout signals to analyze today.")
        return

    feed = BinanceFeed()
    print(f"🔍 Analyzing {len(res.data)} TIMEOUT signals for near-misses...")
    print("=" * 120)
    print(f"{'ID':<8} | {'Side':<4} | {'Entry':<8} | {'TP':<8} | {'Max Pips Fav':<12} | {'Max Pips Adv':<12} | {'Dist to TP'}")
    print("-" * 120)

    # Fetch large batch of 1m candles (1000 candles covers ~16 hours)
    candles = feed.get_history(symbol="EURUSD", interval="1m", limit=1000)
    if not candles:
        print("Failed to fetch historical candles.")
        return

    for s in res.data:
        try:
            entry = float(s['entry_price'])
            tp = float(s['tp'])
            sl = float(s['sl'])
            side = s['direction']
            start_time = datetime.fromisoformat(s['generated_at'].replace('Z', '+00:00'))
            # Timeout is 90 mins after generation or entry_hit? 
            # In SignalWatcher: (now - start_time) >= 90 where start_time is entry_hit_at or generated_at.
            # Most TIMEOUT signals here likely didn't even hit entry OR hit entry and then drifted.
            
            end_time = datetime.fromisoformat(s['closed_at'].replace('Z', '+00:00')) if s.get('closed_at') else start_time + timedelta(minutes=90)
            
            # Filter relevant candles
            relevant = []
            for c in candles:
                c_time = datetime.fromisoformat(c['datetime'].replace('Z', '+00:00'))
                if start_time <= c_time <= end_time:
                    relevant.append(c)
            
            if not relevant:
                print(f"{s['id'][:8]:<8} | Price data gap for this period.")
                continue

            max_favorable_pips = 0
            max_adverse_pips = 0
            
            if side == "BUY":
                highest = max(float(c['high']) for c in relevant)
                lowest = min(float(c['low']) for c in relevant)
                max_favorable_pips = (highest - entry) / 0.0001
                max_adverse_pips = (entry - lowest) / 0.0001
                dist_to_tp = (tp - highest) / 0.0001
            else: # SELL
                lowest = min(float(c['low']) for c in relevant)
                highest = max(float(c['high']) for c in relevant)
                max_favorable_pips = (entry - lowest) / 0.0001
                max_adverse_pips = (highest - entry) / 0.0001
                dist_to_tp = (lowest - tp) / 0.0001

            print(f"{s['id'][:8]:<8} | {side:<4} | {entry:<8.5f} | {tp:<8.5f} | {max_favorable_pips:<12.2f} | {max_adverse_pips:<12.2f} | {dist_to_tp:.2f} pips")
            
        except Exception as e:
            print(f"Error analyzing {s['id']}: {e}")

analyze_timeout_signals()
