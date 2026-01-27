import requests

URL = "https://signalgeniusai-production.up.railway.app/signal/latest"

try:
    resp = requests.get(URL, timeout=10)
    if resp.ok:
        data = resp.json()
        print(f"✅ Success! Connected.")
        print(f"Asset: {data.get('asset')}")
        print(f"Strategy: {data.get('strategy')}")
        print(f"Time: {data.get('timestamp')}")
        print(f"Full Body: {data}")
    else:
        print(f"❌ Error: {resp.status_code}")
        print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
