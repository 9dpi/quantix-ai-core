import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- FETCHING TABLE STRUCTURE ---")
try:
    # Just fetch one row to see columns
    res_log = supabase.table("fx_analysis_log").select("*").limit(1).execute()
    if res_log.data:
        print(f"Log Columns: {list(res_log.data[0].keys())}")
    
    res_sig = supabase.table("fx_signals").select("*").limit(1).execute()
    if res_sig.data:
        print(f"Signal Columns: {list(res_sig.data[0].keys())}")
        
except Exception as e:
    print(f"Error: {e}")
