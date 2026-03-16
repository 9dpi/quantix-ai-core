
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- SIGNAL FREQUENCY CHECK ---")
try:
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    res = supabase.table("fx_signals").select("generated_at").gte("generated_at", today).execute()
    signals = res.data or []
    
    hours = {}
    for s in signals:
        h = s['generated_at'][:13]
        hours[h] = hours.get(h, 0) + 1
        
    for h, count in sorted(hours.items()):
        print(f"Hour: {h}:00 UTC | Count: {count}")

except Exception as e:
    print(f"Error: {e}")
