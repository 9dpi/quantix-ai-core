
import asyncio
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def expire_old():
    print("Expiring old ACTIVE signals...")
    try:
        # Update status to EXPIRED for any ACTIVE signal older than 1 hour
        res = db.client.table(settings.TABLE_SIGNALS)\
            .update({"status": "EXPIRED"})\
            .eq("status", "ACTIVE")\
            .execute()
        print(f"Success! Expired {len(res.data) if res.data else 0} signals.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(expire_old())
