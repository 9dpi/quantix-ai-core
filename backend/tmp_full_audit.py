import requests
import json
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db

def run_audit():
    print("="*60)
    print(f"QUANTIX E2E AUDIT - {datetime.now(timezone.utc).isoformat()}")
    print("="*60)

    # 1. Railway API
    try:
        r = requests.get('https://quantixapiserver-production.up.railway.app/api/v1/health', timeout=10)
        print(f"✅ Railway API: {r.status_code}")
        print(f"   Payload: {r.json()}")
    except Exception as e:
        print(f"❌ Railway API Error: {e}")

    # 2. Supabase Heartbeats
    print("\n--- Supabase Heartbeats (Last 20m) ---")
    since = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
    try:
        res = db.client.table('fx_analysis_log').select('timestamp, asset, status').gte('timestamp', since).order('timestamp', desc=True).limit(10).execute()
        if res.data:
            for r in res.data:
                print(f"[{r['timestamp']}] {r['asset']:20} -> {r['status']}")
        else:
            print("⚠️ No heartbeats found in last 20 minutes.")
    except Exception as e:
        print(f"❌ Supabase Error: {e}")

    # 3. Recent Signals
    print("\n--- Recent Signals (Last 2h) ---")
    h2_since = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    try:
        res_sig = db.client.table('fx_signals').select('id, asset, direction, generated_at, status, tp, sl').gte('generated_at', h2_since).execute()
        print(f"Signals Count: {len(res_sig.data)}")
        for s in res_sig.data:
            print(f"[{s['generated_at']}] {s['asset']} {s['direction']:4} {s['status']:15} | TP:{s['tp']} SL:{s['sl']}")
    except Exception as e:
        print(f"❌ Signal Audit Error: {e}")

    # 4. Bridge Connectivity
    print("\n--- MT4 Bridge Sync Check ---")
    try:
        headers = {'Authorization': 'Bearer DEMO_MT4_TOKEN_2026'}
        r = requests.get('https://quantixapiserver-production.up.railway.app/api/v1/mt4/signals/pending', headers=headers, timeout=10)
        print(f"✅ Bridge API: {r.status_code}")
        print(f"   Response: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"❌ Bridge Auth Error: {e}")

    print("="*60)

if __name__ == "__main__":
    run_audit()
