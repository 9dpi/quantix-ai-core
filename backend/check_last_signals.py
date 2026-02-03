
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def main():
    print("Checking last 5 signals...")
    try:
        res = db.client.table(settings.TABLE_SIGNALS).select("id, asset, direction, state, generated_at, telegram_message_id").order("generated_at", desc=True).limit(5).execute()
        if res.data:
            for sig in res.data:
                msg_id = sig.get('telegram_message_id', 'None')
                print(f"[{sig['generated_at']}] {sig['asset']} {sig['direction']} State: {sig['state']} TG ID: {msg_id}")
        else:
            print("No signals found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
