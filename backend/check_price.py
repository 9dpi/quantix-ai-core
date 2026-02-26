
import requests
import os

def get_current_price():
    api_key = "4a64fb7beafc42e6a9d6b0576ce5cf9f"
    url = f"https://api.twelvedata.com/price?symbol=EUR/USD&apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"Current EUR/USD Price: {data.get('price')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_current_price()
