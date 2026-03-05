import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

# Get the IMPORT_FAIL entries
res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .eq("direction", "CRASH")\
    .order("timestamp", desc=True)\
    .limit(10)\
    .execute()

print("=== ALL CRASH LOGS ===")
for r in res.data:
    print(f"{r['timestamp']} | {r['asset']} | {r['status']}")

# Also check the SYSTEM_WEB entries
print("\n=== SYSTEM_WEB LOGS ===")
res2 = db.client.table("fx_analysis_log")\
    .select("timestamp, direction, status")\
    .eq("asset", "SYSTEM_WEB")\
    .order("timestamp", desc=True)\
    .limit(10)\
    .execute()

for r in res2.data:
    print(f"{r['timestamp']} | {r['direction']} | {r['status']}")
