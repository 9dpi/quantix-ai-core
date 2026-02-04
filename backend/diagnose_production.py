
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
    try:
        stuck_prepared_limit = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        stuck_prepared = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .eq("state", "PREPARED")\
            .lt("generated_at", stuck_prepared_limit)\
            .execute()
        results['atomic_transitions'] = (len(stuck_prepared.data) == 0)
    except:
        results['atomic_transitions'] = False

    # 4. Pipe Cleanliness (WAITING_FOR_ENTRY but no Telegram ID)
    try:
        zombies = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .eq("state", "WAITING_FOR_ENTRY")\
            .is_("telegram_message_id", "null")\
            .execute()
        results['pipe_cleanliness'] = (len(zombies.data) == 0)
    except:
        results['pipe_cleanliness'] = False

    # 5. Fail-Closed Safety (Check if Heartbeat is recently active)
    try:
        # Check audit log timestamp (last 5 mins)
        recent_limit = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        logs = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("timestamp")\
            .order("timestamp", desc=True)\
            .limit(1)\
            .execute()
        
        if logs.data:
            last_ts = datetime.fromisoformat(logs.data[0]['timestamp'].replace('Z', '+00:00'))
            is_active = (datetime.now(timezone.utc) - last_ts).total_seconds() < 300
            results['fail_closed'] = is_active
        else:
            results['fail_closed'] = False
    except:
        results['fail_closed'] = False

    # 6. Trade Flow Integrity (Check for stuck active trades > 4 hours)
    try:
        stuck_trade_limit = (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        stuck_trades = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .eq("state", "ENTRY_HIT")\
            .lt("generated_at", stuck_trade_limit)\
            .execute()
        results['trade_flow'] = (len(stuck_trades.data) == 0)
    except:
        results['trade_flow'] = False

    # 7. Signal Age Distribution (Is the latest signal too old?)
    age_warn = False
    try:
        latest = db.client.table(settings.TABLE_SIGNALS)\
            .select("generated_at")\
            .order("generated_at", desc=True)\
            .limit(1)\
            .execute()
        if latest.data:
            last_sig_ts = datetime.fromisoformat(latest.data[0]['generated_at'].replace('Z', '+00:00'))
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
    print("=" * 25)
    print(f"[{get_status_icon(results.get('db_conn'))}] Database Connectivity")
    print(f"[{get_status_icon(results.get('state_invariants'))}] State Invariants")
    print(f"[{get_status_icon(results.get('atomic_transitions'))}] Atomic Transitions")
    print(f"[{get_status_icon(results.get('pipe_cleanliness'))}] Pipe Cleanliness")
    print(f"[{get_status_icon(results.get('fail_closed'))}] Fail-Closed Safety")
    print(f"[{get_status_icon(results.get('trade_flow'))}] Trade Flow Integrity")
    print("-" * 25)
    print(f"[{'WARN' if age_warn else 'OK'}] Signal Age Distribution")
    print("-" * 25)
    print(f"[INFO] External API Status: {'OK' if api_ok else 'FAIL'}")
    
    avg_latency = sum(latencies.values()) / len(latencies) if latencies else 0
    print(f"[INFO] System Latency: {avg_latency:.0f}ms")
    print("=" * 25)
    
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
