
import asyncio
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def check_columns():
    print("Checking fx_signals columns...")
    try:
        # Fetch one row to see columns
        res = db.client.table(settings.TABLE_SIGNALS).select("*").limit(1).execute()
        if res.data:
            print(f"Columns: {res.data[0].keys()}")
        else:
            print("No data in table.")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
