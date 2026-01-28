
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

async def main():
    today = datetime.now(timezone.utc).date().isoformat()
    print(f"Checking all signals for {today}...")
    try:
        res = db.client.table(settings.TABLE_SIGNALS).select("*").gte("generated_at", today).execute()
        if res.data:
            for sig in res.data:
                print(f"[{sig['generated_at']}] {sig['asset']} {sig['direction']} Conf: {sig['ai_confidence']} Status: {sig['status']}")
        else:
            print("No signals found for today.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
