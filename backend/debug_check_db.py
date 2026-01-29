
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def check():
    res_sig = db.client.table(settings.TABLE_SIGNALS).select("*").order("generated_at", desc=True).limit(5).execute()
    res_log = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").limit(1).execute()
    
    print(f"--- DATABASE STATUS ---")
    print(f"Analysis Log first item: {res_log.data[0]['timestamp'] if res_log.data else 'None'}")
    print(f"Recent Signals:")
    if res_sig.data:
        for s in res_sig.data:
            print(f"- {s.get('id')}: {s.get('generated_at')} | Status: {s.get('status')} | Direction: {s.get('direction')}")
    else:
        print("No signals found.")

if __name__ == "__main__":
    asyncio.run(check())
