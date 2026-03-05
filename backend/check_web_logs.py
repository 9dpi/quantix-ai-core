import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

# Check SYSTEM_WEB and CRASH logs
for asset in ["SYSTEM_WEB", "CRASH", "SYSTEM_ANALYZER"]:
    res = db.client.table("fx_analysis_log")\
        .select("timestamp, asset, direction, status")\
        .eq("asset", asset)\
        .order("timestamp", desc=True)\
        .limit(5)\
        .execute()
    
    if res.data:
        print(f"\n=== {asset} ===")
        for r in res.data:
            print(f"  {r['timestamp']} | {r['direction']} | {r['status']}")
    else:
        print(f"\n=== {asset} === (No data)")

# Also check the latest 15 logs
print("\n=== LATEST 15 LOGS ===")
res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .order("timestamp", desc=True)\
    .limit(15)\
    .execute()
for r in res.data:
    print(f"  {r['timestamp']} | {r['asset']:<20} | {r['direction']:<10} | {r['status'][:60]}")
