
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- RECENT SIGNALS (Last 10) ---")
try:
    res = supabase.table("fx_signals").select("id, asset, direction, state, release_confidence, generated_at, telegram_message_id").order("generated_at", desc=True).limit(10).execute()
    if res.data:
        for s in res.data:
            print(f"ID: {s['id']}, Asset: {s['asset']}, Dir: {s['direction']}, State: {s['state']}, Conf: {s['release_confidence']}, Time: {s['generated_at']}, TG_ID: {s['telegram_message_id']}")
    else:
        print("No signals found.")
except Exception as e:
    print(f"Error: {e}")
