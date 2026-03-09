
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def hunt_rejections():
    print("--- 🎯 Rejection Message Hunt ---")
    try:
        # Fetch status logs that are long enough to be full log lines
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").eq("asset", "ANALYZER_LOG").order("timestamp", desc=True).limit(100).execute()
        logs = res.data or []
        
        keywords = ["sideways", "SKIP_SIGNAL", "ANTI-BURST", "threshold", "Score below", "Birth Signal", "SUCCESS"]
        
        for l in logs:
            status = l.get("status", "")
            # Check if any keyword matches
            if any(k.lower() in status.lower() for k in keywords):
                ts = l.get("timestamp", "")[11:19]
                print(f"[{ts}] {status[:200]}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    hunt_rejections()
