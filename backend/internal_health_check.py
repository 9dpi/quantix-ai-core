
import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from quantix_core.database.connection import db

def check_health():
    print("--- QUANTIX COMPREHENSIVE HEALTH CHECK ---")
    now = datetime.now(timezone.utc)
    print(f"Current UTC: {now.isoformat()}\n")
    
    target_assets = [
        "SYSTEM_ANALYZER", 
        "HEARTBEAT", 
        "HEARTBEAT_WATCHER", 
        "VALIDATOR", 
        "SYSTEM_WEB",
        "SYSTEM_WATCHDOG",
        "WATCHDOG_ALERT"
    ]
    
    print(f"{'ASSET':<20} | {'AGE (min)':<10} | {'STATUS'}")
    print("-" * 70)
    
    for asset in target_assets:
        try:
            res = db.client.table("fx_analysis_log")\
                .select("*")\
                .eq("asset", asset)\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            
            if res.data:
                log = res.data[0]
                ts_str = log.get("timestamp")
                status = str(log.get("status"))[:40] # Truncate
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                age = (now - ts).total_seconds() / 60
                
                status_icon = "🟢" if age < 30 else "🟡" if age < 120 else "🔴"
                print(f"{status_icon} {asset:<18} | {age:<10.1f} | {status}")
            else:
                print(f"⚪ {asset:<18} | {'N/A':<10} | No data found")
                
        except Exception as e:
            print(f"❌ {asset:<18} | {'Error':<10} | {e}")

    # --- Log Sniffing ---
    print("\n--- RECENT SERVICE LOGS (Live Stream) ---")
    
    # 1. Uvicorn (Web)
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("direction", "UVICORN_LOG")\
            .order("timestamp", desc=True)\
            .limit(3)\
            .execute()
        print(f"\n>> UVICORN_LOG:")
        if res.data:
            for log in reversed(res.data):
                print(f"   [{log['timestamp'][11:19]}] {log['status'][:120]}")
        else:
            print("   (No logs found)")
    except: pass

    # 2. Analyzer
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("asset", "ANALYZER_LOG")\
            .order("timestamp", desc=True)\
            .limit(3)\
            .execute()
        print(f"\n>> ANALYZER_LOG:")
        if res.data:
            for log in reversed(res.data):
                print(f"   [{log['timestamp'][11:19]}] {log['status'][:120]}")
        else:
            print("   (No logs found)")
    except: pass

    # 3. Watcher
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("asset", "WATCHER_LOG")\
            .order("timestamp", desc=True)\
            .limit(3)\
            .execute()
        print(f"\n>> WATCHER_LOG:")
        if res.data:
            for log in reversed(res.data):
                print(f"   [{log['timestamp'][11:19]}] {log['status'][:120]}")
        else:
            print("   (No logs found)")
    except: pass

    # 4. Validator
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("asset", "VALIDATOR_LOG")\
            .order("timestamp", desc=True)\
            .limit(3)\
            .execute()
        print(f"\n>> VALIDATOR_LOG:")
        if res.data:
            for log in reversed(res.data):
                print(f"   [{log['timestamp'][11:19]}] {log['status'][:120]}")
        else:
            print("   (No logs found)")
    except: pass

    # 5. Watchdog
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("asset", "WATCHDOG_LOG")\
            .order("timestamp", desc=True)\
            .limit(3)\
            .execute()
        print(f"\n>> WATCHDOG_LOG:")
        if res.data:
            for log in reversed(res.data):
                print(f"   [{log['timestamp'][11:19]}] {log['status'][:120]}")
        else:
            print("   (No logs found)")
    except: pass

if __name__ == "__main__":
    check_health()
