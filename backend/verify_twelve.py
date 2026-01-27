import os
import requests
import sys

# Hardcoded key from .env
API_KEY = "4a64fb7beafc42e6a9d6b0576ce5cf9f"
BASE_URL = "https://api.twelvedata.com"

def test_key():
    print(f"Testing Twelve Data API Key: {API_KEY[:4]}...{API_KEY[-4:]}")
    
    # 1. Test Price Endpoint
    try:
        url = f"{BASE_URL}/price"
        params = {"symbol": "EUR/USD", "apikey": API_KEY}
        print(f"Requesting: {url}...")
        resp = requests.get(url, params=params, timeout=10)
        
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Success! EUR/USD Price: {data.get('price')}")
        else:
            print(f"❌ Failed! Response: {resp.text}")
            
    except Exception as e:
        print(f"❌ Exception during request: {e}")

if __name__ == "__main__":
    test_key()
