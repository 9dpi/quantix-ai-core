import sys
sys.path.append("d:\\Automator_Prj\\Quantix_AI_Core\\backend")
from quantix_core.database.connection import db
import datetime

try:
    sig = {
        'asset': 'EURUSD', 
        'direction': 'BUY', 
        'state': 'ACTIVE', 
        'generated_at': datetime.datetime.utcnow().isoformat(), 
        'tp': 1.1600, 
        'sl': 1.1500,
        'entry_price': 1.1550,
        'timeframe': 'M15',
        'is_test': True
    }
    print("Inserting...")
    res = db.client.table('fx_signals').insert(sig).execute()
    print("SUCCESS")
except Exception as e:
    print("ERROR", str(e))
