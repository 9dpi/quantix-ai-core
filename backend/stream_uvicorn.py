import os, sys, time
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

print("=== LIVE UVICORN LOGS ===")
seen = set()
while True:
    try:
        res = db.client.table("fx_analysis_log")\
            .select("timestamp, status")\
            .eq("asset", "UVICORN_LOG")\
            .order("timestamp", desc=True)\
            .limit(10)\
            .execute()
        
        # Sort chronologically
        logs = sorted(res.data, key=lambda x: x['timestamp'])
        for r in logs:
            row_id = f"{r['timestamp']}-{r['status'][:20]}"
            if row_id not in seen:
                print(f"[{r['timestamp'][11:19]}] {r['status']}")
                seen.add(row_id)
        
        time.sleep(3)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(3)
