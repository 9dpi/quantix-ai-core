
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def analyze_recent_logs():
    print("--- 🔍 Analyzing Recent Analysis Cycles ---")
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").order("timestamp", desc=True).limit(20).execute()
        logs = res.data or []
        
        if not logs:
            print("No analysis logs found.")
            return

        for s in reversed(logs):
            ts = s.get("timestamp", "")[11:19]
            price = s.get("price", 0)
            conf = s.get("confidence", 0)
            status = s.get("status", "")
            asset = s.get("asset", "")
            direction = s.get("direction", "")
            
            print(f"[{ts}] {asset:<15} | Price: {price:<8.5f} | Conf: {conf:<5.2f} | Status: {status}")
            
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    analyze_recent_logs()
