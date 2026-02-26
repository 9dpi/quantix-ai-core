from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

def get_logs():
    since = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
    res = db.client.table('fx_analysis_log').select('*').gte('timestamp', since).order('timestamp', desc=True).execute()
    
    print(f"{'Timestamp':<30} | {'Asset':<15} | {'Direction':<12} | {'Status'}")
    print("-" * 100)
    for l in res.data:
        ts = l.get('timestamp', 'N/A')
        asset = l.get('asset', 'N/A')
        direction = l.get('direction', 'N/A')
        status = l.get('status', 'N/A')
        print(f"{ts:<30} | {asset:<15} | {direction:<12} | {status}")

if __name__ == "__main__":
    get_logs()
