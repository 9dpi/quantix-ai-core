
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone

async def check_recent_global():
    # Last 20 signals regardless of date
    res = db.client.table('fx_signals')\
        .select('id, status, state, generated_at, ai_confidence, strategy, telegram_message_id')\
        .order('generated_at', desc=True)\
        .limit(20)\
        .execute()
    
    print(f"Most recent 20 signals:")
    for s in res.data:
        print(f"ID: {s['id'][:8]} | Status: {s['status']:10} | State: {s['state']:15} | Conf: {s.get('ai_confidence', 'N/A')} | TG: {s.get('telegram_message_id')} | Time: {s['generated_at']}")

if __name__ == "__main__":
    asyncio.run(check_recent_global())
