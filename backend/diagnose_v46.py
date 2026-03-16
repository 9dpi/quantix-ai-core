import os
import sys
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.getcwd())
try:
    from quantix_core.database.connection import db
    from quantix_core.config.settings import settings
except Exception as e:
    print(f"Import failed: {e}")
    sys.exit(1)

print(f"--- DIAGNOSTICS v4.6 ---")
print(f"Time: {datetime.now(timezone.utc).isoformat()}")

try:
    print(f"Checking table: {settings.TABLE_ANALYSIS_LOG}")
    res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").order("timestamp", desc=True).limit(10).execute()
    if res.data:
        print(f"Last 10 logs in {settings.TABLE_ANALYSIS_LOG}:")
        for x in res.data:
            print(f"{x['timestamp']} | {x['asset']} | {x['status'][:100]}")
    else:
        print("No logs found in DB.")
except Exception as e:
    print(f"DB Query Failed: {e}")

try:
    print(f"\nChecking signals table: {settings.TABLE_SIGNALS}")
    res = db.client.table(settings.TABLE_SIGNALS).select("*").order("generated_at", desc=True).limit(5).execute()
    if res.data:
        print(f"Last 5 signals:")
        for x in res.data:
            print(f"{x['generated_at']} | {x['status']} | {x.get('asset')} | {x.get('direction')}")
    else:
        print("No signals found in DB.")
except Exception as e:
    print(f"DB Query Failed: {e}")
