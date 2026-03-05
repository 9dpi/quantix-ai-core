import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

res = db.client.table("fx_analysis_log")\
    .select("timestamp, direction, status")\
    .eq("asset", "SYSTEM_WEB")\
    .order("timestamp", desc=True)\
    .limit(20)\
    .execute()

print("=== ALL SYSTEM_WEB LOGS ===")
for r in res.data:
    print(f"[{r['timestamp']}] {r['direction']:<12} | {r['status'][:200]}")
