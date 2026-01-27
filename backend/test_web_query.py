import requests
import os

# Testing local mock of what Railway is doing
URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals?select=*&status=eq.ACTIVE&order=generated_at.desc&limit=1"
KEY = "PASTE_KEY_HERE" # Need to be careful not to log/expose, but I need to test if the query itself is valid

def test_query():
    # I'll use the KEY from env since I'm running locally
    from dotenv import load_dotenv
    load_dotenv(override=True)
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    headers = {
        "apikey": key, 
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    print(f"Testing direct Supabase query...")
    resp = requests.get(URL, headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")

if __name__ == "__main__":
    test_query()
