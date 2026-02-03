
import asyncio
from quantix_core.database.connection import db

async def check():
    res = db.client.table('fx_signals').select('id, status, state, generated_at').in_('status', ['PUBLISHED', 'ACTIVE', 'ENTRY_HIT']).execute()
    print(f"Total active/published: {len(res.data)}")
    for s in res.data:
        print(f"ID: {s['id'][:8]} | Status: {s['status']:10} | State: {s['state']:15} | Time: {s['generated_at']}")

if __name__ == "__main__":
    asyncio.run(check())
