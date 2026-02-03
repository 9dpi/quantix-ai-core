
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone

async def check_heartbeat():
    res = db.client.table('fx_analysis_log')\
        .select('*')\
        .order('timestamp', desc=True)\
        .limit(5)\
        .execute()
    
    print(f"Recent heartbeats:")
    for h in res.data:
        print(f"Time: {h['timestamp']} | Conf: {h.get('confidence')} | Release Conf: {h.get('release_confidence')}")

if __name__ == "__main__":
    asyncio.run(check_heartbeat())
