
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

def check_stuck():
    print("--- 🕵️ Stuck Signal Audit ---")
    now = datetime.now(timezone.utc)
    
    res = db.client.table(settings.TABLE_SIGNALS).select("*").in_(
        "state", ["WAITING_FOR_ENTRY", "ENTRY_HIT", "ACTIVE", "PUBLISHED", "PENDING"]
    ).execute()
    
    signals = res.data or []
    print(f"Active/Pending signals in DB: {len(signals)}")
    
    stuck_found = False
    for s in signals:
        gen_at = datetime.fromisoformat(s['generated_at'].replace("Z", "+00:00"))
        age_min = (now - gen_at).total_seconds() / 60
        
        status = "OK"
        if s['state'] in ["WAITING_FOR_ENTRY", "PUBLISHED"] and age_min > 40:
            status = "🚨 STUCK (Pending > 40m)"
            stuck_found = True
        elif s['state'] in ["ENTRY_HIT", "ACTIVE"] and age_min > 160:
            status = "🚨 STUCK (Trade > 160m)"
            stuck_found = True
            
        print(f"ID: {s['id'][:8]} | State: {s['state']:<18} | Age: {age_min:>5.1f}m | Status: {status}")
        
    if not stuck_found:
        print("✅ No signals appear to be stuck according to age thresholds.")
    else:
        print("❌ Stuck signals detected!")

if __name__ == "__main__":
    check_stuck()
