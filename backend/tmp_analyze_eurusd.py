
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def analyze_eurusd_logs():
    print("--- 🔍 Analyzing Recent EURUSD Analysis Cycles ---")
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").eq("asset", "EURUSD").order("timestamp", desc=True).limit(10).execute()
        logs = res.data or []
        
        if not logs:
            print("No EURUSD analysis logs found.")
            return

        for s in reversed(logs):
            ts = s.get("timestamp", "")[11:19]
            price = s.get("price", 0)
            conf = s.get("confidence", 0)
            rel_conf = s.get("release_confidence", 0)
            status = s.get("status", "")
            refinement = s.get("refinement", "")
            
            print(f"[{ts}] EURUSD | Price: {price:<8.5f} | Raw Conf: {conf:<5.2f} | Rel Conf: {rel_conf:<5.2f}")
            print(f"    Refinement: {refinement}")
            
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    analyze_eurusd_logs()
