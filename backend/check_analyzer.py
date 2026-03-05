import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .in_("asset", ["SYSTEM_ANALYZER", "HEARTBEAT"])\
    .order("timestamp", desc=True)\
    .limit(15)\
    .execute()

print("=== ANALYZER & HEARTBEAT LOGS ===")
for r in res.data:
    print(f"[{r['timestamp'][11:19]}] {r['asset']:15} | {r['direction']:10} | {str(r['status'])[:100]}")
