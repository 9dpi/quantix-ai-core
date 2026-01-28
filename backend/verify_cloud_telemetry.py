
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def main():
    try:
        data = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").limit(5).execute()
        print(f"Count: {len(data.data) if data.data else 0}")
        if data.data:
            print(data.data[0])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
