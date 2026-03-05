import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db
import textwrap

res = db.client.table("fx_analysis_log")\
    .select("timestamp, asset, direction, status")\
    .eq("direction", "CRASH")\
    .order("timestamp", desc=True)\
    .limit(3)\
    .execute()

print("--- RECENT CRASHES ---")
for r in res.data:
    print(f"[{r['timestamp']}] {r['asset']}")
    print(textwrap.shorten(r['status'], width=100))
    print("-" * 50)
