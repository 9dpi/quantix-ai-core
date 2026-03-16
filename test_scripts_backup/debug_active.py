
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- ACTIVE SIGNALS CHECK ---")
try:
    res = supabase.table("fx_signals").select("id, asset, direction, generated_at").in_("state", ["WAITING_FOR_ENTRY", "ENTRY_HIT"]).execute()
    signals = res.data or []
    print(f"Active Signals: {len(signals)}")
    for s in signals:
        print(f"ID: {s['id']}, {s['asset']} {s['direction']}, Time: {s['generated_at']}")
except Exception as e:
    print(f"Error: {e}")
