import requests
import json
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from quantix_core.feeds.binance_feed import BinanceFeed

def check_flow():
    print("="*60)
    print(f"QUANTIX DATA FLOW AUDIT - {datetime.now(timezone.utc).isoformat()}")
    print("="*60)

    # 1. DATA SOURCE CHECK (Binance as proxy for market volatility)
    print("\n[Step 1] Data Source (Binance Feed)...")
    try:
        feed = BinanceFeed()
        price = feed.get_current_price("EURUSDT") # EURUSDT on Binance
        print(f"✅ Binance Feed: EURUSDT = {price}")
    except Exception as e:
        print(f"❌ Data Source Error: {e}")

    # 2. ANALYZER HEARTBEAT (Railway Processing)
    print("\n[Step 2] Analyzer Heartbeat (Cloud Process)...")
    since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    try:
        res = db.client.table('fx_analysis_log').select('timestamp, status').eq('asset', 'HEARTBEAT_ANALYZER').gte('timestamp', since).order('timestamp', desc=True).limit(1).execute()
        if res.data:
            hb = res.data[0]
            print(f"✅ Analyzer Heartbeat: {hb['timestamp']} -> {hb['status']}")
            diff = (datetime.now(timezone.utc) - datetime.fromisoformat(hb['timestamp'].replace('Z', '+00:00'))).total_seconds()
            print(f"   (Staleness: {diff:.1f}s)")
        else:
            print("❌ STUCK: No analyzer heartbeat in last 15 minutes!")
    except Exception as e:
        print(f"❌ Heartbeat Check Error: {e}")

    # 3. ANALYSIS ENGINE (Decision Making)
    print("\n[Step 3] Analysis Engine (EURUSD Logs)...")
    try:
        res = db.client.table('fx_analysis_log').select('timestamp, status, confidence').eq('asset', 'EURUSD').order('timestamp', desc=True).limit(3).execute()
        if res.data:
            for r in res.data:
                print(f"✅ EURUSD Analysis: {r['timestamp']} | Conf: {r['confidence']} | {r['status']}")
        else:
            print("⚠️ No EURUSD analysis logs found.")
    except Exception as e:
        print(f"❌ Analysis Log Error: {e}")

    # 4. MT4 BRIDGE (Execution Gateway)
    print("\n[Step 4] MT4 Bridge Connectivity...")
    try:
        headers = {'Authorization': 'Bearer DEMO_MT4_TOKEN_2026'}
        r = requests.get('https://quantixapiserver-production.up.railway.app/api/v1/mt4/signals/pending', headers=headers, timeout=10)
        print(f"✅ Bridge Status: {r.status_code}")
        data = r.json()
        print(f"   Signals Pending for MT4: {data.get('count', 0)}")
        if data.get('signals'):
             for s in data['signals']:
                 print(f"   - {s['signal_id']}: {s['order_type']} {s['symbol']} @ {s.get('entry_price', 'Market')}")
    except Exception as e:
        print(f"❌ Bridge Connection Error: {e}")

    print("\n" + "="*60)
    print("CONCLUSION:")
    if diff < 120:
        print("🚀 [HEALTHY] Data is flowing, Analyzer is ticking, Bridge is open.")
    else:
        print("⚠️ [STAGNANT] System seems alive but heartbeat is stale. Check Railway logs.")
    print("="*60)

if __name__ == "__main__":
    check_flow()
