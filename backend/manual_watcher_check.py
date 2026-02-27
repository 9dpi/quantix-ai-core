
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from quantix_core.database.connection import db
from quantix_core.engine.signal_watcher import SignalWatcher
from quantix_core.ingestion.twelve_data_client import TwelveDataClient
from quantix_core.config.settings import settings

def run_once():
    td_client = TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
    watcher = SignalWatcher(
        supabase_client=db.client,
        td_client=td_client,
        check_interval=1
    )
    print("Starting manual check cycle...")
    watcher.check_cycle()
    print("Cycle complete.")

if __name__ == "__main__":
    run_once()
