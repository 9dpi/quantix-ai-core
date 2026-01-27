import requests

URL = "https://signalgeniusai-production.up.railway.app/health"

try:
    print(f"Fetching health from {URL}...")
    resp = requests.get(URL, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
