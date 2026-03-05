import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db
from loguru import logger
logger.remove()

print("=== UVICORN OUTPUT LOGS ===")
res = db.client.table("fx_analysis_log")\
    .select("timestamp, status")\
    .eq("direction", "SELF_PING")\
    .order("timestamp", desc=True)\
    .limit(20)\
    .execute()

logs = sorted(res.data, key=lambda x: x['timestamp'])
with open("uvicorn_dump.txt", "w", encoding="utf-8") as f:
    for r in logs:
        f.write(f"[{r['timestamp'][11:19]}] {r['status']}\n")
print("Logs dumped to uvicorn_dump.txt")
