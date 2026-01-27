import requests

URL = "https://signalgeniusai-production.up.railway.app/signal/latest"

try:
    print(f"Fetching from {URL}...")
    resp = requests.get(URL, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
