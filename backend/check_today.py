
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone

async def check_today_signals():
    today = datetime.now(timezone.utc).date().isoformat()
    res = db.client.table('fx_signals')\
        .select('id, status, generated_at, release_confidence, strategy')\
        .gte('generated_at', today)\
        .order('generated_at', desc=True)\
        .execute()
    
    print(f"Signals found today: {len(res.data)}")
    for s in res.data:
        print(f"ID: {s['id'][:8]} | Status: {s['status']:10} | Score: {s.get('release_confidence', 'N/A')} | Strategy: {s.get('strategy', 'N/A')} | Time: {s['generated_at']}")

if __name__ == "__main__":
    asyncio.run(check_today_signals())
