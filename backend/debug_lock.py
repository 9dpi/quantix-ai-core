
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(os.getcwd()) / 'backend'))
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer

def debug_lock():
    analyzer = ContinuousAnalyzer()
    print("Testing lock_signal with dummy data...")
    test_signal = {
        "asset": "EURUSD",
        "direction": "SELL",
        "timeframe": "M15",
        "generated_at": "2026-03-02T10:00:00Z",
        "ai_confidence": 0.96,
        "release_confidence": 0.96,
        "status": "PUBLISHED",
        "state": "ENTRY_HIT",
        "is_market_entry": True,
        "is_test": True,
        "entry_price": 1.1000,
        "tp": 1.0900,
        "sl": 1.1100,
        "explainability": "Debug Lock Test"
    }
    
    try:
        res = db.client.table(settings.TABLE_SIGNALS).insert(test_signal).execute()
        print(f"Success! Signal ID: {res.data[0]['id']}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    debug_lock()
