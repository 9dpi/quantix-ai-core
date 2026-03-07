import uuid
from datetime import datetime, timezone
from quantix_core.database.connection import db

def run_test():
    print("Injecting PARTIAL_CLOSE signal for testing...")
    
    unique_id = str(uuid.uuid4())
    
    mock_signal = {
        "id": unique_id,
        "asset": "TEST_PARTIAL",
        "direction": "BUY",  
        "entry_price": 1.0500,
        "tp": 1.0600,
        "sl": 1.0400,
        "state": "CANCELLED",
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    
    response = db.client.table("fx_signals").insert(mock_signal).execute()
    print(f"Injected Signal ID: {unique_id}")
    print("MT4 EA should pick this up on its next polling cycle (within 5 seconds).")

if __name__ == "__main__":
    run_test()
