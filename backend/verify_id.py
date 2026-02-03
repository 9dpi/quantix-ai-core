
import asyncio
from quantix_core.database.connection import db

async def verify_id(sid):
    res = db.client.table('fx_signals').select('*').eq('id', sid).execute()
    if res.data:
        s = res.data[0]
        print(f"ID: {s['id']} | Status: {s['status']} | State: {s['state']} | TG: {s['telegram_message_id']} | Entry: {s['entry_price']} | Time: {s['generated_at']}")
    else:
        print("Signal not found")

if __name__ == "__main__":
    import sys
    sid = "71295ccc-3cbe-4120-b08b-8bec73f17c6b"
    asyncio.run(verify_id(sid))
