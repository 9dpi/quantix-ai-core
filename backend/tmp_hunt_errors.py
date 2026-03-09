
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def hunt_errors():
    print("--- 🕵️ Error Hunt (14:18 UTC) ---")
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").eq("asset", "ANALYZER_LOG").gte("timestamp", "2026-03-09T14:18:00").order("timestamp").execute()
        logs = res.data or []
        
        for l in logs:
            status = l.get("status", "")
            if any(k in status for k in ["❌", "⚠️", "Failed", "Error", "exception"]):
                print(f"[{l['timestamp'][11:19]}] {status}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    hunt_errors()
