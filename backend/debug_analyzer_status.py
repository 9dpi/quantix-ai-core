import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

def debug_analyzer():
    print("=== ANALYZER DETAILED LOG AUDIT ===")
    res = db.client.table("fx_analysis_log")\
        .select("timestamp, status")\
        .eq("asset", "ANALYZER_LOG")\
        .order("timestamp", desc=True)\
        .limit(30)\
        .execute()
    
    if not res.data:
        print("No ANALYZER_LOG found.")
        return

    for r in res.data:
        ts = r['timestamp'][11:19]
        status = r['status']
        # Filter for interesting bits
        if any(x in status for x in ["Signal", "SKIP", "REJECT", "cooldown", "Market closed"]):
            print(f"[{ts}] {status}")
        elif "final state" in status.lower():
            print(f"[{ts}] {status}")

if __name__ == "__main__":
    debug_analyzer()
