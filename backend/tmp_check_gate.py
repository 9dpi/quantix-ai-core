
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def check_gate_and_signals():
    print("--- 🛡️ Gate & Signal Check ---")
    try:
        # 1. Check for recent signals
        res = db.client.table(settings.TABLE_SIGNALS).select("*").order("generated_at", desc=True).limit(5).execute()
        signals = res.data or []
        print(f"Recent signals in DB:")
        for s in signals:
            print(f"ID: {s['id'][:8]} | State: {s['state']:<18} | GenAt: {s['generated_at']}")
            
        # 2. Check for gate rejections in analysis logs
        # We search logs with 'Status: ANALYZED' and look into 'refinement' or just generally look at the last few logs
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").order("timestamp", desc=True).limit(50).execute()
        logs = res.data or []
        
        rejection_found = False
        for l in logs:
            status = l.get("status", "")
            if "[ANTI-BURST]" in status or "[GATE]" in status:
                print(f"Found rejection log: {l['timestamp']} | {status}")
                rejection_found = True
        
        if not rejection_found:
            print("No explicit gate rejection logs found in last 50 entries.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_gate_and_signals()
