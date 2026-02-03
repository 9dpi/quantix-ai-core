
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

async def main():
    today = datetime.now(timezone.utc).date().isoformat()
    print(f"Checking analysis logs for {today}...")
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("timestamp, asset, status").gte("timestamp", today).order("timestamp", desc=True).limit(5).execute()
        if res.data:
            for log in res.data:
                print(f"[{log['timestamp']}] {log['asset']} Status: {log['status']}")
        else:
            print("No analysis logs found for today.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
