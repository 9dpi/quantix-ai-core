from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

five_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
res = db.client.table("fx_analysis_log").select("asset, timestamp, status").gte("timestamp", five_min_ago).execute()

for r in res.data:
    print(f"[{r['timestamp']}] {r['asset']}: {r['status']}")
