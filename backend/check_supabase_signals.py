
import asyncio
import os
import json
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def main():
    print("Checking Supabase signals...")
    try:
        data = db.client.table(settings.TABLE_SIGNALS).select("*").order("generated_at", desc=True).limit(5).execute()
        if data.data:
            for sig in data.data:
                print(f"[{sig['generated_at']}] {sig['asset']} {sig['direction']} Entry: {sig['entry_low']} Status: {sig['status']}")
        else:
            print("No signals found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
