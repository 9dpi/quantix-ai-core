
import requests
import json
from datetime import datetime, timezone

def check_price_history():
    api_key = '4a64fb7beafc42e6a9d6b0576ce5cf9f'
    url = 'https://api.twelvedata.com/time_series'
    params = {
        'symbol': 'EUR/USD',
        'interval': '1min',
        'outputsize': 120,
        'apikey': api_key
    }
    
    r = requests.get(url, params=params)
    data = r.json()
    
    if data.get('status') != 'ok':
        print(f"Error: {data}")
        return
        
    print(f"{'Time (UTC)':20} | {'Low':10} | {'High':10}")
    print("-" * 45)
    
    found_hit = False
    for v in data.get('values', []):
        t = v['datetime']
        low = float(v['low'])
        high = float(v['high'])
        print(f"{t:20} | {low:10.5f} | {high:10.5f}")
        
        # 1.1822 was the entry for the 9:06 signal (BUY)
        if low <= 1.1822:
            found_hit = True
            
    print("-" * 45)
    print(f"Did price ever touch 1.1822? {'YES' if found_hit else 'NO'}")

if __name__ == "__main__":
    check_price_history()
