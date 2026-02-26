from quantix_core.database.connection import db
res = db.client.table('fx_signals').select('*').order('generated_at', desc=True).limit(1).execute()
if res.data:
    s = res.data[0]
    entry = float(s['entry_price'])
    tp = float(s['tp'])
    sl = float(s['sl'])
    tp_pips = abs(tp - entry) / 0.0001
    sl_pips = abs(sl - entry) / 0.0001
    print(f"ID: {s['id']}")
    print(f"Asset: {s['asset']}")
    print(f"Side: {s.get('direction')}")
    print(f"Status: {s.get('status')} | State: {s.get('state')}")
    print(f"Entry: {entry}")
    print(f"TP: {tp} ({tp_pips:.1f} pips)")
    print(f"SL: {sl} ({sl_pips:.1f} pips)")
    print(f"Total Amplitude (SL to TP): {abs(tp - sl) / 0.0001:.1f} pips")
else:
    print("No signals found.")
