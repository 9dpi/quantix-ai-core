import os
import sys
from datetime import datetime, timezone

# Add backend to path
project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

from quantix_core.config.settings import settings
from quantix_core.notifications.telegram_notifier_v2 import TelegramNotifierV2

print(f"Testing Telegram Notifier with CHAT_ID: {settings.TELEGRAM_CHAT_ID}")
notifier = TelegramNotifierV2(
    bot_token=settings.TELEGRAM_BOT_TOKEN,
    chat_id=settings.TELEGRAM_CHAT_ID,
    admin_chat_id=settings.TELEGRAM_ADMIN_CHAT_ID
)

test_signal = {
    "id": "test_manual_id",
    "asset": "EURUSD",
    "timeframe": "M15",
    "direction": "BUY",
    "entry_price": 1.12345,
    "tp": 1.12445,
    "sl": 1.12245,
    "release_confidence": 0.95,
    "is_market_entry": True,
    "is_test": True
}

print("Pushing test signal...")
msg_id = notifier.send_market_execution(test_signal)
print(f"Result (msg_id): {msg_id}")

if msg_id:
    print("✅ SUCCESS: Telegram message sent.")
else:
    print("❌ FAILED: Telegram message NOT sent.")
