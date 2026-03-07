import uuid
import json
from datetime import datetime, timezone
from quantix_core.database.connection import db

def run_real_test():
    """
    Spawns a signal in the database specifically crafted to trigger 
    a PARTIAL_CLOSE action on an active EURUSD trade in MT4.
    """
    print("🚀 Preparing REAL Partial Close Signal for EURUSD...")
    print("Requirement: You must have an active EURUSD trade with Magic Number 900900 in MT4.")
    
    unique_id = str(uuid.uuid4())
    
    # We craft the metadata to tell the API it's a PARTIAL_CLOSE action
    metadata = {
        "action": "PARTIAL_CLOSE",
        "close_lots": 0.05
    }
    
    real_signal = {
        "id": unique_id,
        "asset": "EURUSD",
        "direction": "BUY",  # Doesn't matter much for Partial Close if Symbol/Magic matches
        "entry_price": 1.0500,
        "tp": 1.0600,
        "sl": 1.0400,
        "state": "CANCELLED", # The API is currently tuned to pick up CANCELLED signals for dev testing
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metadata": json.dumps(metadata)
    }
    
    try:
        response = db.client.table("fx_signals").insert(real_signal).execute()
        print(f"✅ Signal Injected! UUID: {unique_id}")
        print("MT4 EA should pick this up in ~1 second via http://127.0.0.1/api/v1/mt4/signals/pending")
        print("Please check your MT4 'Trade' and 'Experts' tabs.")
    except Exception as e:
        print(f"❌ Error injecting signal: {e}")

if __name__ == "__main__":
    run_real_test()
