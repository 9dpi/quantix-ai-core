
from quantix_core.database.connection import db
import json

def analyze():
    # Fetch recent signals
    res = db.client.table('fx_signals').select('*').order('generated_at', desc=True).limit(20).execute()
    signals = res.data
    
    # Fetch MT4 callbacks
    res_cb = db.client.table('fx_analysis_log').select('*').eq('asset', 'MT4_CALLBACK').order('timestamp', desc=True).limit(20).execute()
    callbacks = res_cb.data
    
    print("--- RECENT SIGNALS ---")
    for s in signals:
        print(f"ID: {s['id'][:8]} | Entry: {s['entry_price']} | SL: {s['sl']} | TP: {s['tp']} | State: {s['state']} | Created: {s['generated_at']}")
    
    print("\n--- MT4 CALLBACKS ---")
    for cb in callbacks:
        try:
            status = json.loads(cb['status'])
            # Status might be a dict or a string depending on how it was logged
            if isinstance(status, dict):
                print(f"Ticket: {status.get('ticket')} | Asset: {status.get('symbol')} | Type: {status.get('type')} | Price: {status.get('price')} | Time: {cb['timestamp']}")
            else:
                print(f"CB: {status} | Time: {cb['timestamp']}")
        except:
            print(f"Raw Status: {cb['status']} | Time: {cb['timestamp']}")

if __name__ == '__main__':
    analyze()
