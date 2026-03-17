import os
import sys
from datetime import datetime, timezone

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from quantix_core.database.connection import db

def dump_logs():
    print("Dumping last 100 ANALYZER_LOG entries...")
    res = db.client.table("fx_analysis_log").select("timestamp, status").eq("asset", "ANALYZER_LOG").order("timestamp", desc=True).limit(100).execute()
    
    with open("analyzer_dump.txt", "w", encoding="utf-8") as f:
        for s in res.data:
            f.write(f"{s['timestamp']} | {s['status']}\n")
    print(f"Dumped {len(res.data)} logs to analyzer_dump.txt")

if __name__ == "__main__":
    dump_logs()
