
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def check_today_signals():
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        res = db.client.table(settings.TABLE_SIGNALS)\
            .select("id,asset,direction,generated_at,state")\
            .gte("generated_at", today)\
            .execute()
        
        if not res.data:
            print(f"No signals generated today ({today}) in Supabase.")
            return

        print(f"Signals generated today ({today}):")
        print("-" * 80)
        for s in res.data:
            print(f"{s['generated_at']} | {s['id']} | {s['asset']} {s['direction']} | State: {s['state']}")
        
    except Exception as e:
        print(f"Error checking signals: {e}")

if __name__ == "__main__":
    asyncio.run(check_today_signals())
