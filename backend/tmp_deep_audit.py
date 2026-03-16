"""Deep audit: Why 91% confidence didn't produce more signals on Mar 11"""
from quantix_core.database.connection import db

def deep_audit():
    # 1. HIDDEN_DEBUG signals (prepared but not released)
    res = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%HIDDEN%')\
     .order('timestamp', desc=True).limit(20).execute()
    print(f"--- HIDDEN_DEBUG signals: {len(res.data)} ---")
    for r in res.data:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    # 2. PREPARED signals (ready but gated)
    res2 = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .ilike('status', '%PREPARED%')\
     .order('timestamp', desc=True).limit(20).execute()
    print(f"\n--- PREPARED signals: {len(res2.data)} ---")
    for r in res2.data:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    # 3. Non-ANALYZED entries (everything except ANALYZED)
    res3 = db.client.table('fx_analysis_log').select(
        'timestamp, status, confidence'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .neq('status', 'ANALYZED')\
     .order('timestamp', desc=True).limit(30).execute()
    print(f"\n--- Non-ANALYZED entries: {len(res3.data)} ---")
    for r in res3.data:
        print(f"  {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")

    # 4. Status distribution count
    all_res = db.client.table('fx_analysis_log').select(
        'status'
    ).eq('asset', 'EURUSD')\
     .gte('timestamp', '2026-03-11T00:00:00Z')\
     .lt('timestamp', '2026-03-12T00:00:00Z')\
     .execute()
    
    status_counts = {}
    for r in all_res.data:
        s = r['status']
        status_counts[s] = status_counts.get(s, 0) + 1
    
    print(f"\n--- STATUS DISTRIBUTION (Total: {len(all_res.data)}) ---")
    for s, c in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"  {s:40} -> {c}")

if __name__ == '__main__':
    deep_audit()
