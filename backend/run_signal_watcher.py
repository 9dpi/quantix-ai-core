"""
Run Signal Watcher

Starts the signal watcher loop to monitor active signals
and perform state transitions.
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
from loguru import logger
from supabase import create_client
from twelvedata import TDClient

from quantix_core.engine.signal_watcher import SignalWatcher

# Load environment variables
load_dotenv()

def main():
    """Initialize and run signal watcher"""
    
    # Configure logging
    logger.add(
        "logs/signal_watcher_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    logger.info("=" * 60)
    logger.info("SIGNAL WATCHER STARTING")
    logger.info("=" * 60)
    
    # Initialize Supabase client
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY in environment")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    logger.success("✅ Supabase client initialized")
    
    # Initialize TwelveData client
    td_api_key = os.getenv("TWELVE_DATA_API_KEY")
    
    if not td_api_key:
        logger.error("Missing TWELVE_DATA_API_KEY in environment")
        sys.exit(1)
    
    td_client = TDClient(apikey=td_api_key)
    logger.success("✅ TwelveData client initialized")
    
    # Get configuration
    check_interval = int(os.getenv("WATCHER_CHECK_INTERVAL", "60"))
    
    logger.info(f"Check interval: {check_interval} seconds")
    
    # Initialize watcher
    watcher = SignalWatcher(
        supabase_client=supabase,
        td_client=td_client,
        check_interval=check_interval
    )
    
    logger.success("✅ SignalWatcher initialized")
    
    # Run watcher loop
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Watcher stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Watcher crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
