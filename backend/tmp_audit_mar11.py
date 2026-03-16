"""Audit: Why only 2 signals on March 11?"""
from quantix_core.database.connection import db
from datetime import datetime, timezone

def audit():
    print("="*60)
    print("AUDIT: March 11, 2026 — Signal Generation Report")
    print("="*60)

    # 1. Signals generated
    res = db.client.table('fx_signals').select(
        'id, asset, direction, generated_at, status, tp, sl, ai_confidence'
    ).gte('generated_at', '2026-03-11T00:00:00Z')\
     .lt('generated_at', '2026-03-12T00:00:00Z')\
     .order('generated_at', desc=True).execute()

    print(f"\n--- 1. SIGNALS GENERATED: {len(res.data)} ---")
    for s in res.data:
        tp_pips = round(abs(s['tp'] - float(s.get('entry_price', s['tp']))) * 10000, 1) if s.get('entry_price') else '?'
        sl_pips = round(abs(s['sl'] - float(s.get('entry_price', s['sl']))) * 10000, 1) if s.get('entry_price') else '?'
        print(f"  {s['generated_at']} | {s['direction']:4} | {s['status']:18} | Conf: {s['ai_confidence']} | TP:{s['tp']} SL:{s['sl']}")

    # 2. Analyzer cycles (EURUSD only)
    res2 = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .order('timestamp', desc=True).limit(30).execute()

    print(f"\n--- 2. ANALYZER CYCLES (EURUSD): {len(res2.data)} entries ---")
    for r in res2.data:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    # 3. Gate rejections (look for BLOCKED or COOLDOWN)
    res3 = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%BLOCK%')\
     .order('timestamp', desc=True).limit(20).execute()

    res3b = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%COOLDOWN%')\
     .order('timestamp', desc=True).limit(20).execute()

    res3c = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%GATE%')\
     .order('timestamp', desc=True).limit(20).execute()

    blocks = (res3.data or []) + (res3b.data or []) + (res3c.data or [])
    print(f"\n--- 3. GATE REJECTIONS: {len(blocks)} entries ---")
    for r in sorted(blocks, key=lambda x: x['timestamp'], reverse=True)[:15]:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    # 4. Circuit breaker events
    res4 = db.client.table('fx_analysis_log').select(
        'timestamp, status'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%CIRCUIT%')\
     .order('timestamp', desc=True).limit(10).execute()

    print(f"\n--- 4. CIRCUIT BREAKER EVENTS: {len(res4.data)} ---")
    for r in res4.data:
        print(f"  {r['timestamp']} | {r['status']}")

    # 5. Heartbeat count (is analyzer alive?)
    res5 = db.client.table('fx_analysis_log').select(
        'timestamp'
    ).eq('asset', 'HEARTBEAT_ANALYZER')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .execute()

    print(f"\n--- 5. ANALYZER HEARTBEATS: {len(res5.data)} ---")
    if res5.data:
        print(f"  First: {res5.data[-1]['timestamp']}")
        print(f"  Last:  {res5.data[0]['timestamp']}")

    # 6. Low confidence rejections
    res6 = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%LOW%')\
     .order('timestamp', desc=True).limit(15).execute()

    print(f"\n--- 6. LOW CONFIDENCE REJECTIONS: {len(res6.data)} ---")
    for r in res6.data:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    print("\n" + "="*60)

if __name__ == '__main__':
    audit()
