
import asyncio
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from quantix_core.engine.signal_watcher import SignalWatcher
from twelvedata import TDClient

async def main():
    td_client = TDClient(apikey=settings.TWELVE_DATA_API_KEY)
    watcher = SignalWatcher(
        supabase_client=db.client,
        td_client=td_client,
        check_interval=60
    )
    
    print("🚀 Running manual check cycle...")
    watcher.check_cycle()
    print("✅ Done.")

if __name__ == "__main__":
    asyncio.run(main())
