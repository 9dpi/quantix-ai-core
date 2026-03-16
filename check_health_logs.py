
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- FETCHING RECENT HEALTH REPORTS ---")
try:
    res = supabase.table("fx_analysis_log").select("*").eq("asset", "HEALTH_REPORT").order("timestamp", desc=True).limit(5).execute()
    if res.data:
        for row in res.data:
            print(f"Time: {row['timestamp']}, Status: {row['status']}, Asset: {row['asset']}")
    else:
        print("No HEALTH_REPORT entries found.")
        
    print("\n--- FETCHING RECENT ERRORS ---")
    res_err = supabase.table("fx_analysis_log").select("*").ilike("status", "%fail%").order("timestamp", desc=True).limit(5).execute()
    if res_err.data:
        for row in res_err.data:
            print(f"Time: {row['timestamp']}, Status: {row['status']}, Asset: {row['asset']}")
    else:
        print("No recent errors found in logs.")

except Exception as e:
    print(f"Error: {e}")
