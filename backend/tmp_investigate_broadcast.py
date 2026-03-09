
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def investigate_signal():
    print("--- 🕵️ Signal Broadcast Investigation ---")
    try:
        # 1. Fetch the exact signal born around 14:18 UTC
        res = db.client.table(settings.TABLE_SIGNALS).select("*").gte("generated_at", "2026-03-09T14:18:00").execute()
        signals = res.data or []
        
        if not signals:
            print("❌ Critical: No signal found in DB for 14:18 UTC!")
            return

        for s in signals:
            print(f"ID: {s['id']} | State: {s['state']} | TG_ID: {s.get('telegram_message_id')} | GenAt: {s['generated_at']}")
            
        # 2. Check for related logs in ANALYZER_LOG after 14:18:29
        print("\n--- Related Logs ---")
        res_logs = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").eq("asset", "ANALYZER_LOG").gte("timestamp", "2026-03-09T14:18:29").order("timestamp").execute()
        logs = res_logs.data or []
        for l in logs:
            print(f"[{l['timestamp'][11:19]}] {l['status']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    investigate_signal()
