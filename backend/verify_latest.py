
import asyncio
from quantix_core.database.connection import db

async def verify_last():
    res = db.client.table('fx_signals').select('*').order('generated_at', desc=True).limit(1).execute()
    if res.data:
        s = res.data[0]
        print(f"ID: {s['id']} | Status: {s['status']} | State: {s['state']} | TG: {s['telegram_message_id']} | Entry: {s['entry_price']} | Time: {s['generated_at']}")
    else:
        print("No signals found")

if __name__ == "__main__":
    asyncio.run(verify_last())
