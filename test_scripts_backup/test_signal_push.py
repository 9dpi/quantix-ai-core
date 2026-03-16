
import os
import sys
from datetime import datetime, timezone
import json

# Add backend to path
project_root = "d:/Automator_Prj/Quantix_AI_Core"
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
from quantix_core.config.settings import settings

print("🚀 Testing Manual Signal Push...")

try:
    analyzer = ContinuousAnalyzer()
    
    # Fake signal data based on the one we found
    signal_data = {
        "id": "c240f880-a4b9-42fb-b87a-061177602bb8",
        "asset": "EURUSD",
        "direction": "BUY",
        "timeframe": "M5",
        "entry_price": 1.1440,
        "tp": 1.1450,
        "sl": 1.1435,
        "release_confidence": 0.95,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "is_test": True
    }
    
    print(f"Pushing signal {signal_data['id']} to Telegram...")
    msg_id = analyzer.push_to_telegram(signal_data)
    
    if msg_id:
        print(f"✅ Success! Sent with ID: {msg_id}")
    else:
        print("❌ Failed: push_to_telegram returned None")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
