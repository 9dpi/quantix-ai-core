from quantix_core.database.connection import db
import sys

sig_id = 'a667de47-721c-40a1-990b-84642cc5dc0e'
try:
    res = db.client.table("fx_signals").select("id, asset, direction, entry_price, tp, sl, state, status, result").eq("id", sig_id).execute()
    if res.data:
        s = res.data[0]
        print(f"Signal ID: {s.get('id')}")
        print(f"Asset: {s.get('asset')}")
        print(f"State: {s.get('state')}")
        print(f"Status: {s.get('status')}")
        print(f"Result: {s.get('result')}")
        print(f"Entry: {s.get('entry_price')}")
        print(f"TP: {s.get('tp')}")
        print(f"SL: {s.get('sl')}")
    else:
        print("Signal not found.")
except Exception as e:
    print(f"Error: {e}")
