import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

# Get SYSTEM_WEB entries
res = db.client.table("fx_analysis_log")\
    .select("timestamp, direction, status")\
    .eq("asset", "SYSTEM_WEB")\
    .order("timestamp", desc=True)\
    .limit(15)\
    .execute()

from loguru import logger
logger.remove() # Suppress loguru interference

print("=== SYSTEM_WEB TIMELINE ===")
for r in res.data:
    ts = r['timestamp']
    d = r['direction']
    s = str(r['status'])[:100]
    print(f"{ts} | {d:<15} | {s}")
