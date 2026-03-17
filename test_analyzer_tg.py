import os
import sys
from datetime import datetime, timezone

# Add backend to path
project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
from quantix_core.config.settings import settings

print("Initializing ContinuousAnalyzer for Diagnostic Alert...")
analyzer = ContinuousAnalyzer()

test_signal = {
    "asset": "DIAGNOSTIC",
    "timeframe": "M15",
    "direction": "BUY",
    "entry_price": 1.1500,
    "tp": 1.1510,
    "sl": 1.1495,
    "release_confidence": 0.99,
    "is_market_entry": True,
    "is_test": True
}

print("Running push_to_telegram directly from Analyzer context...")
msg_id = analyzer.push_to_telegram(test_signal)
print(f"Result (msg_id): {msg_id}")

if msg_id:
    print("✅ SUCCESS: Telegram message sent from Analyzer context.")
else:
    print("❌ FAILED: Telegram message NOT sent from Analyzer context.")
