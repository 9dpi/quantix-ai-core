
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
import json

def check_mt4():
    print("--- 🤖 MT4 Bridge Audit ---")
    
    # 1. Check latest signals in pending/active status
    print("\n[Latest Signals for MT4 Fetch]")
    res_sig = db.client.table("fx_signals").select("*").in_("status", ["WAITING_FOR_ENTRY", "ENTRY_HIT", "PUBLISHED"]).order("generated_at", desc=True).limit(5).execute()
    for s in res_sig.data:
        print(f"ID: {s['id']} | Status: {s['status']} | State: {s['state']} | GenAt: {s['generated_at']}")
        
    # 2. Check MT4 callbacks
    print("\n[Latest MT4 Callbacks]")
    res_cb = db.client.table("fx_analysis_log").select("*").eq("asset", "MT4_CALLBACK").order("timestamp", desc=True).limit(10).execute()
    for c in res_cb.data:
        print(f"[{c['timestamp']}] {c['status']} | {c['direction']}")

if __name__ == "__main__":
    check_mt4()
