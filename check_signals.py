from quantix_core.database.connection import db

res = db.client.table('fx_signals').select('id, direction, entry_price, tp, sl, status, generated_at').order('generated_at', desc=True).limit(8).execute()

for r in res.data:
    entry = r['entry_price']
    tp = r['tp']
    sl = r['sl']
    dir = r['direction']
    
    if dir == 'SELL':
        tp_dist = round((entry - tp) * 10000, 1)
        sl_dist = round((sl - entry) * 10000, 1)
    else:
        tp_dist = round((tp - entry) * 10000, 1)
        sl_dist = round((entry - sl) * 10000, 1)
    
    print(f"{r['generated_at'][:19]} | {dir} | Entry: {entry} | TP: {tp} ({tp_dist}p) | SL: {sl} ({sl_dist}p) | {r['status']}")
