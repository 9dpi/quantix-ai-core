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

from quantix_core.config.settings import settings
from quantix_core.engine.signal_watcher import SignalWatcher

def main():
    """Initialize and run signal watcher"""
    
    # Configure logging
    logger.add(
        "logs/signal_watcher_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )
    
    logger.info("============================================================")
    instance_name = settings.INSTANCE_NAME
    logger.info(f"SIGNAL WATCHER STARTING - INSTANCE: {instance_name}")
    logger.info("============================================================")
    
    # Initialize Supabase client
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY in environment")
        sys.exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    logger.success("✅ Supabase client initialized")
    
    # Initialize TwelveData client
    td_api_key = settings.TWELVE_DATA_API_KEY
    
    if not td_api_key:
        logger.error("Missing TWELVE_DATA_API_KEY in environment")
        sys.exit(1)
    
    td_client = TDClient(apikey=td_api_key)
    logger.success("✅ TwelveData client initialized")
    
    # Initialize Telegram notifier
    telegram_token = settings.TELEGRAM_BOT_TOKEN
    telegram_chat_id = settings.TELEGRAM_CHAT_ID
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    
    telegram_notifier = None
    if telegram_token and telegram_chat_id:
        from quantix_core.notifications.telegram_notifier_v2 import TelegramNotifierV2
        telegram_notifier = TelegramNotifierV2(telegram_token, telegram_chat_id, admin_chat_id)
        logger.success(f"✅ Telegram notifier initialized (Admin: {admin_chat_id})")
    else:
        logger.warning("⚠️  Telegram credentials not found, notifications disabled")
    
    # Get configuration
    check_interval = settings.WATCHER_CHECK_INTERVAL
    observe_mode = settings.WATCHER_OBSERVE_MODE
    
    logger.info(f"Check interval: {check_interval} seconds")
    logger.info(f"Observe mode: {observe_mode}")
    
    # Force disable Telegram in observe mode (GATE 3)
    if observe_mode:
        telegram_notifier = None
        logger.warning("🔍 OBSERVE MODE: Telegram notifications DISABLED")
        logger.info("Only logging state transitions to verify correctness")
    
    # Initialize watcher
    watcher = SignalWatcher(
        supabase_client=supabase,
        td_client=td_client,
        check_interval=check_interval,
        telegram_notifier=telegram_notifier
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
