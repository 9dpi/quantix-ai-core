
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- RECENT ANALYZER LOGS (Around 02:02 UTC) ---")
try:
    # Fetch logs between 02:00 and 02:05 UTC
    res = supabase.table("fx_analysis_log").select("*")\
        .gte("timestamp", "2026-03-16T02:00:00")\
        .lte("timestamp", "2026-03-16T02:10:00")\
        .order("timestamp", desc=False).execute()
    if res.data:
        for row in res.data:
            print(f"Time: {row['timestamp']}, Status: {row['status']}, Asset: {row['asset']}")
    else:
        print("No logs found in that range.")
except Exception as e:
    print(f"Error: {e}")
