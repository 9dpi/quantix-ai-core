import requests
from datetime import datetime, timezone

def check_history():
    # EURUSDT 15m klines from 01:30 UTC today
    # 01:30 UTC is approx 1740360600000ms
    url = "https://api.binance.com/api/v3/klines"
    import time
    start_time = int((time.time() - 15 * 3600) * 1000)
    params = {
        "symbol": "EURUSDT",
        "interval": "15m",
        "startTime": start_time, 
        "limit": 100
    }
    
    resp = requests.get(url, params=params)
    data = resp.json()
    
    if isinstance(data, dict):
        print(f"API Error: {data}")
        return

    print(f"{'Time (UTC)':<20} | {'High':<8} | {'Low':<8} | {'Close':<8}")
    print("-" * 50)
    
    entry_price = 1.17794
    tp = 1.17644
    sl = 1.17944
    
    entry_hit = False
    
    for k in data:
        ts = datetime.fromtimestamp(k[0]/1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        high = float(k[2])
        low = float(k[3])
        close = float(k[4])
        
        print(f"{ts:<20} | {high:<8} | {low:<8} | {close:<8}")
        
        if not entry_hit:
            if low <= entry_price:
                print(f" >>> [ENTRY HIT] at {ts}")
                entry_hit = True
        else:
            if high >= sl:
                print(f" !!! [SL HIT] at {ts} (High: {high})")
                # break # Continue to see if TP also hit or status
            if low <= tp:
                print(f" $$$ [TP HIT] at {ts} (Low: {low})")
                # break

if __name__ == "__main__":
    check_history()
