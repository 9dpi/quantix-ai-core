
import asyncio
import os
import requests
import time
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

def get_status_icon(success, warn=False):
    if success: return "OK"
    if warn: return "WARN"
    return "FAIL"

async def run_diagnostics():
    results = {}
    latencies = {}
    
    # 1. Database Connectivity
    start = time.time()
    try:
        db.client.table(settings.TABLE_SIGNALS).select("count", count="exact").limit(1).execute()
        latencies['db'] = (time.time() - start) * 1000
        results['db_conn'] = True
    except:
        results['db_conn'] = False

    # 2. State Invariants (Check for records with missing critical fields)
    try:
        bad_records = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .is_("state", "null")\
            .execute()
        results['state_invariants'] = (len(bad_records.data) == 0)
    except:
        results['state_invariants'] = False

    # 3. Atomic Transitions (Check for signals stuck in PREPARED phase)
    stuck_prepared_ids = []
    try:
        stuck_prepared_limit = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        stuck_prepared = db.client.table(settings.TABLE_SIGNALS)\
            .select("id, asset")\
            .eq("state", "PREPARED")\
            .lt("generated_at", stuck_prepared_limit)\
            .execute()
        stuck_prepared_ids = stuck_prepared.data if stuck_prepared.data else []
        results['atomic_transitions'] = (len(stuck_prepared_ids) == 0)
    except:
        results['atomic_transitions'] = False

    # 4. Pipe Cleanliness (WAITING_FOR_ENTRY but no Telegram ID)
    zombie_ids = []
    try:
        zombies = db.client.table(settings.TABLE_SIGNALS)\
            .select("id, asset")\
            .eq("state", "WAITING_FOR_ENTRY")\
            .is_("telegram_message_id", "null")\
            .execute()
        zombie_ids = zombies.data if zombies.data else []
        results['pipe_cleanliness'] = (len(zombie_ids) == 0)
    except:
        results['pipe_cleanliness'] = False

    # 4.1 Stuck Pending Signals (WAITING_FOR_ENTRY > 30 mins)
    stuck_pending_ids = []
    try:
        stuck_pending_limit = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        stuck_pending = db.client.table(settings.TABLE_SIGNALS)\
            .select("id, asset, generated_at")\
            .eq("state", "WAITING_FOR_ENTRY")\
            .lt("generated_at", stuck_pending_limit)\
            .execute()
        stuck_pending_ids = stuck_pending.data if stuck_pending.data else []
        results['stuck_pending'] = (len(stuck_pending_ids) == 0)
    except:
        results['stuck_pending'] = False

    # 5. Fail-Closed Safety (Check if Heartbeat is recently active)
    last_hb_ts = "N/A"
    try:
        logs = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("timestamp")\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()
        
        if logs.data:
            last_hb_ts = logs.data[0]['timestamp']
            last_ts = datetime.fromisoformat(last_hb_ts.replace('Z', '+00:00'))
            is_active = (datetime.now(timezone.utc) - last_ts).total_seconds() < 300
            results['fail_closed'] = is_active
        else:
            results['fail_closed'] = False
    except:
        results['fail_closed'] = False

    # 6. Trade Flow Integrity (Check for stuck active trades > 90 mins)
    stuck_trade_ids = []
    try:
        stuck_trade_limit = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
        stuck_trades = db.client.table(settings.TABLE_SIGNALS)\
            .select("id, asset")\
            .eq("state", "ENTRY_HIT")\
            .lt("generated_at", stuck_trade_limit)\
            .execute()
        stuck_trade_ids = stuck_trades.data if stuck_trades.data else []
        results['trade_flow'] = (len(stuck_trade_ids) == 0)
    except:
        results['trade_flow'] = False

    # 7. Signal Age Distribution (Is the latest signal too old?)
    age_warn = False
    last_sig_text = "N/A"
    try:
        latest = db.client.table(settings.TABLE_SIGNALS)\
            .select("generated_at, asset")\
            .order("generated_at", desc=True)\
            .limit(1)\
            .execute()
        if latest.data:
            last_sig_ts = datetime.fromisoformat(latest.data[0]['generated_at'].replace('Z', '+00:00'))
            last_sig_text = f"{latest.data[0]['asset']} at {last_sig_ts.strftime('%H:%M UTC')}"
            age_hours = (datetime.now(timezone.utc) - last_sig_ts).total_seconds() / 3600
            if age_hours > 24:
                age_warn = True
    except:
        age_warn = True

    # 8. External API Status
    api_ok = True
    # TwelveData
    start = time.time()
    try:
        url = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&outputsize=1&apikey={settings.TWELVE_DATA_API_KEY}"
        res = requests.get(url, timeout=5)
        latencies['twelve'] = (time.time() - start) * 1000
        if not (res.status_code == 200 and res.json().get("status") == "ok"):
            api_ok = False
    except:
        api_ok = False
        
    # Telegram
    start = time.time()
    try:
        res = requests.get(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
        latencies['telegram'] = (time.time() - start) * 1000
        if res.status_code != 200:
            api_ok = False
    except:
        api_ok = False

    # OUTPUT
    print("\nQUANTIX SYSTEM DIAGNOSTICS")
    print("=" * 60)
    print(f"[{get_status_icon(results.get('db_conn'))}] Database Connectivity")
    print(f"[{get_status_icon(results.get('state_invariants'))}] State Invariants")
    
    print(f"[{get_status_icon(results.get('atomic_transitions'))}] Atomic Transitions (PREPARED < 10m)")
    if stuck_prepared_ids:
        for s in stuck_prepared_ids: print(f"    -> STUCK PREPARED: {s['asset']} ({s['id']})")
        
    print(f"[{get_status_icon(results.get('pipe_cleanliness'))}] Pipe Cleanliness (WAITING but no TG_ID)")
    if zombie_ids:
        for s in zombie_ids: print(f"    -> ZOMBIE: {s['asset']} ({s['id']})")
        
    print(f"[{get_status_icon(results.get('stuck_pending'))}] Stuck Pending Checker (WAITING > 30m)")
    if stuck_pending_ids:
        for s in stuck_pending_ids: print(f"    -> STUCK PENDING: {s['asset']} ({s['id']})")
        
    print(f"[{get_status_icon(results.get('fail_closed'))}] Fail-Closed Safety (Heartbeat < 5m)")
    print(f"    -> Last Heartbeat: {last_hb_ts}")
    
    print(f"[{get_status_icon(results.get('trade_flow'))}] Trade Flow Integrity (ACTIVE > 90m)")
    if stuck_trade_ids:
        for s in stuck_trade_ids: print(f"    -> STUCK TRADE: {s['asset']} ({s['id']})")
        
    print("-" * 60)
    print(f"[{'WARN' if age_warn else 'OK'}] Signal Age Distribution")
    print(f"    -> Latest Signal: {last_sig_text}")
    print("-" * 60)
    print(f"[INFO] External API Status: {'OK' if api_ok else 'FAIL'}")
    
    avg_latency = sum(latencies.values()) / len(latencies) if latencies else 0
    print(f"[INFO] System Latency: {avg_latency:.0f}ms")
    print("=" * 60)
    
    # Verdict Calculation for v3.1 Monitor Orchestration
    # Critical Invariants: DB Connection, State Integrity, Fail-Closed Safety
    critical_invariants = ['db_conn', 'state_invariants', 'fail_closed']
    is_verdict_pass = all(results.get(k, False) for k in critical_invariants)
    
    # Optional logic: include all results in verdict if you want strict safety
    all_clean = all(results.values())
    
    # Output for monitor_streams.bat findstr
    if is_verdict_pass:
        print("SYSTEM_VERDICT=PASS")
    else:
        failed_keys = [k for k, v in results.items() if not v]
        print(f"SYSTEM_VERDICT=FAIL (Breached: {', '.join(failed_keys)})")

    # Detailed Trace for Debugging
    print(f"\n[DEBUG] Latency Trace: DB:{latencies.get('db',0):.0f}ms | TD:{latencies.get('twelve',0):.0f}ms | TG:{latencies.get('telegram',0):.0f}ms")
    print(f"[DEBUG] API Health: TwelveData {'OK' if 'twelve' in latencies and api_ok else 'FAIL'} | Telegram {'OK' if 'telegram' in latencies and api_ok else 'FAIL'}")
    print(f"[DEBUG] Last Heartbeat Audit: {'OK' if results.get('fail_closed') else 'STALE/MISSING'}")
    print(f"[DEBUG] Check Time: {datetime.now(timezone.utc).isoformat()} UTC\n")

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
