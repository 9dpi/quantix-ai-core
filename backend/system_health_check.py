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
    print("\n--- 📊 Data Source & Quota Usage ---")
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        # Query logs for today
        res = db.client.table("fx_analysis_log").select("status, status").eq("status", "ANALYZED").gte("timestamp", today).execute()
        logs = res.data or []
        count = len(logs)
        
        print(f"Total Analysis Cycles Today: {count}")
        print(f"Primary Source: BINANCE (Free/Unlimited)")
        print(f"Fallback Source: TWELVEDATA (Quota Protected)")
        
        # TwelveData credit tracking (only if fallback was hit)
        # Note: In current implementation, if Binance is Primary, credits are only used if Binance fails.
        print(f"Estimated TwelveData usage: {count} / 800 credits (Max possible if fallback hit)")
        
        if count > 750:
             print("⚠️ NOTE: If TwelveData was used as fallback, it may be near limit.")
        
        print("\n[Current System Status]")
        try:
            res_latest = db.client.table("fx_analysis_log").select("*").eq("asset", "HEARTBEAT_ANALYZER").order("timestamp", desc=True).limit(1).execute()
            if res_latest.data:
                latest = res_latest.data[0]
                print(f"Last Heartbeat: {latest['timestamp'][:19]} | {latest['status']}")
        except: pass
            
    except Exception as e:
        print(f"❌ Quota check failed: {e}")

if __name__ == "__main__":
    print(f"Quantix Health Check - {datetime.now(timezone.utc).isoformat()}")
    check_heartbeats()
    check_analysis()
    check_quota()
