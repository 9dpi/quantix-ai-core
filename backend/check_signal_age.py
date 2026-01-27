import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv(override=True)

URL = os.getenv("SUPABASE_URL")
# Use Service Key to be sure
KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") 

def check_signal_age():
    print(f"Checking ACTIVE signal age at: {URL}")
    url = f"{URL}/rest/v1/fx_signals?select=*&status=eq.ACTIVE&order=generated_at.desc&limit=1"
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        resp = requests.get(url, headers=headers)
        if resp.ok:
            data = resp.json()
            if data:
                sig = data[0]
                gen_time_str = sig['generated_at']
                # Parse ISO format
                gen_time = datetime.fromisoformat(gen_time_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                age_minutes = (now - gen_time).total_seconds() / 60
                
                print(f"✅ Found ACTIVE signal: {sig['id']}")
                print(f"   Generated At: {gen_time_str}")
                print(f"   Current Time: {now.isoformat()}")
                print(f"   Age: {age_minutes:.2f} minutes")
                
                if age_minutes > 90:
                    print("⚠️ Signal is EXPIRED (Age > 90 min) -> Web will hide it.")
                else:
                    print("🟢 Signal is VALID (Age < 90 min) -> Web should show it.")
                    
            else:
                print("❌ No ACTIVE signal found in DB.")
        else:
            print(f"❌ Error querying: {resp.status_code} {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    check_signal_age()
