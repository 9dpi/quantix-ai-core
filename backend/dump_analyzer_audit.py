import os, sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from quantix_core.database.connection import db

def dump_logs():
    print("=== DUMPING ANALYZER_LOGS ===")
    res = db.client.table("fx_analysis_log")\
        .select("timestamp, status")\
        .eq("asset", "ANALYZER_LOG")\
        .order("timestamp", desc=True)\
        .limit(100)\
        .execute()
    
    with open("analyzer_audit_full.txt", "w", encoding="utf-8") as f:
        for r in res.data:
            line = f"[{r['timestamp'][11:19]}] {r['status']}\n"
            f.write(line)
    print("Check analyzer_audit_full.txt")

if __name__ == "__main__":
    dump_logs()
