import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

def check_signals():
    now = datetime.now(timezone.utc)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    res = db.client.table("fx_signals")\
        .select("*")\
        .gte("generated_at", start_of_day.isoformat())\
        .execute()
    
    signals = res.data or []
    print(f"--- SIGNALS BORN TODAY: {len(signals)} ---")
    for s in signals:
        reason = s.get("intelligence_reasoning", "NONE")
        print(f"[{s['generated_at'][11:16]}] {s['asset']:7} | {s['state']:15} | Conf: {s.get('confidence', 0)*100:.0f}% | Reason: {str(reason)[:50]}")

if __name__ == "__main__":
    check_signals()
