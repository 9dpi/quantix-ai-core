import sys
import os
sys.path.append(os.getcwd())
from quantix_core.database.connection import db
from datetime import datetime, timedelta

print("--- RECENT SYSTEM LOGS ---")
res = db.client.table('fx_analysis_log').select('*').order('timestamp', desc=True).limit(30).execute()
for r in res.data:
    print(f"{r['timestamp']} | {r['asset']} | {r['status']} | {r['direction']}")

print("\n--- RECENT SIGNALS ---")
res_sig = db.client.table('fx_signals').select('*').order('generated_at', desc=True).limit(10).execute()
for s in res_sig.data:
    print(f"{s['generated_at']} | {s['asset']} | {s['direction']} | {s['state']} | {s['status']}")
