from quantix_core.database.connection import db
import sys

def check_val(val):
    try:
        db.client.table("validation_events").insert({
            "signal_id": "health_check",
            "asset": "EURUSD",
            "feed_source": "binance_proxy",
            "check_type": val,
            "main_system_state": "WAITING_FOR_ENTRY",
            "validator_price": 1.0,
            "is_discrepancy": False
        }).execute()
        return True
    except Exception as e:
        if "chk_check_type" in str(e):
            return False
        else:
            print(f"Error for {val}: {e}")
            return False

vals = [
    "ENTRY", "TP", "SL", "ENTRY_HIT", "TP_HIT", "SL_HIT",
    "ENTRY_MISMATCH", "TP_MISMATCH", "SL_MISMATCH",
    "MATCH", "DISCREPANCY", "PRICE_MATCH", "WAITING",
    "CHECK", "VALIDATION", "PROOF"
]

print("Testing validation_events check_type values...")
allowed = []
for v in vals:
    if check_val(v):
        allowed.append(v)
        print(f"✅ {v} is ALLOWED")

print(f"\nFinal allowed list: {allowed}")
