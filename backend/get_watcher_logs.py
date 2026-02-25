from quantix_core.database.connection import db
import sys

try:
    res = db.client.table("fx_analysis_log").select("*").eq("asset", "DEBUG_WATCHER").order("timestamp", desc=True).limit(10).execute()
    if res.data:
        print("\n--- Watcher Market Data Logs ---")
        for b in res.data:
            print(f"[{b['timestamp'][:19]}] Price: {b['price']} | Info: {b['direction']}")
    else:
        print("No watcher debug logs found.")
except Exception as e:
    print(f"Error: {e}")
