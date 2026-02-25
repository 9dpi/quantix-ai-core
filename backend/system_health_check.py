import sys
import os
from datetime import datetime, timezone
from loguru import logger

# Add current directory to path
sys.path.append(os.getcwd())

from quantix_core.database.connection import db
from quantix_core.config.settings import settings

def check_heartbeats():
    print("\n--- 💓 System Heartbeats (Last 5) ---")
    
    # 1. Watcher Heartbeats
    print("\n[Watcher Service]")
    try:
        res = db.client.table("fx_analysis_log").select("*").eq("asset", "HEARTBEAT_WATCHER").order("timestamp", desc=True).limit(3).execute()
        if not res.data:
            print("❌ No Watcher heartbeats found!")
        for b in res.data:
            print(f"[{b['timestamp'][:19]}] Status: {b['status']}")
    except Exception as e:
        print(f"❌ Watcher check failed: {e}")

    # 2. Validator Heartbeats
    print("\n[Validator Service]")
    try:
        res = db.client.table("fx_analysis_log").select("*").eq("asset", "VALIDATOR").order("timestamp", desc=True).limit(3).execute()
        if not res.data:
            print("❌ No Validator heartbeats found!")
        for b in res.data:
            print(f"[{b['timestamp'][:19]}] Status: {b['status']}")
    except Exception as e:
        print(f"❌ Validator check failed: {e}")

def check_analysis():
    print("\n--- 🧠 AI Analysis Logs (Last 5) ---")
    try:
        res = db.client.table("fx_analysis_log").select("*").eq("status", "ANALYZED").order("timestamp", desc=True).limit(5).execute()
        if not res.data:
            print("⚪ No analysis logs found for today yet.")
            return
        for b in res.data:
            print(f"[{b['timestamp'][:19]}] {b['asset']} | Price: {b['price']} | {b['direction']}")
    except Exception as e:
        print(f"❌ Analysis log check failed: {e}")

def check_quota():
    print("\n--- 📊 TwelveData Usage ---")
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        res = db.client.table("fx_analysis_log").select("*", count="exact").eq("status", "ANALYZED").gte("timestamp", today).execute()
        count = res.count or 0
        print(f"Estimated Usage Today: {count} / 800 credits")
        if count > 700:
            print("⚠️ WARNING: Approaching daily credit limit!")
    except Exception as e:
        print(f"❌ Quota check failed: {e}")

if __name__ == "__main__":
    print(f"Quantix Health Check - {datetime.now(timezone.utc).isoformat()}")
    check_heartbeats()
    check_analysis()
    check_quota()
