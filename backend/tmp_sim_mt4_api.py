
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
import json
from datetime import datetime, timezone

def sim_api():
    print("--- 📡 Simulating MT4 Pending Signals Query ---")
    res = db.client.table("fx_signals")\
        .select("*")\
        .in_("status", ["WAITING_FOR_ENTRY", "ENTRY_HIT"])\
        .order("generated_at", desc=True)\
        .limit(5)\
        .execute()
    
    signals = res.data
    print(f"Signals found in DB: {len(signals)}")
    
    mt4_payloads = []
    for sig in signals:
        meta = sig.get("metadata", {})
        if isinstance(meta, str):
            try: meta = json.loads(meta)
            except: meta = {}
            
        signal_id = sig.get("id")
        payload = {
            "signal_id": str(signal_id),
            "strategy_id": sig.get("strategy", "Quantix_v4_SMC"),
            "timestamp": sig.get("generated_at"),
            "action": meta.get("action", "EXECUTE_MARKET"),
            "symbol": sig.get("asset", "EURUSD"),
            "order_type": sig.get("direction", "SELL"),
            "sl_price": sig.get("sl"),
            "tp_price": sig.get("tp"),
            "max_spread_pips": 3.0,
            "max_slippage_pips": 5.0
        }
        mt4_payloads.append(payload)
        
    print(json.dumps(mt4_payloads, indent=2))

if __name__ == "__main__":
    sim_api()
