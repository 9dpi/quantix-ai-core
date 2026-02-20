
import time, requests, sys
import os

# Ensure console supports utf-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://quantixaicore-production.up.railway.app/api/v1"

def check_endpoint(name, url):
    try:
        r = requests.get(url, timeout=10)
        status = "✅ OK" if r.status_code == 200 else f"❌ {r.status_code}"
        print(f"{name:<20} | {status:<6} | {url}")
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        print(f"{name:<20} | ❌ ERR | {e}")
        return None

print("=" * 60)
print("QUANTIX AI CORE - SYSTEM HEALTH MONITOR")
print("=" * 60)

# 1. API Root
check_endpoint("API Root", BASE_URL.replace("/api/v1", ""))

# 2. Threads Status
threads_data = check_endpoint("Background Threads", f"{BASE_URL}/health/threads")
if threads_data:
    print("-" * 60)
    print(f"  Validator Thread : {'✅ RUNNING' if threads_data.get('validator_thread_alive') else '❌ STOPPED'}")
    print(f"  Auto-Adjuster    : {'✅ RUNNING' if threads_data.get('auto_adjuster_alive') else '❌ STOPPED'}")
    print(f"  Analyzer (Gen)   : {'✅ RUNNING' if threads_data.get('analyzer_thread_alive') else '❌ STOPPED'}")
    print(f"  Environment      : {threads_data.get('railway_env', 'local')}")
    print("-" * 60)

# 3. Validation Status
val_data = check_endpoint("Validation Status", f"{BASE_URL}/validation-status")
if val_data:
    print(f"  Health           : {val_data.get('health')}")
    print(f"  Discrepancy Rate : {val_data.get('accuracy', {}).get('discrepancy_rate_pct')}%")

# 4. Signals
sig_data = check_endpoint("Signals (Active)", f"{BASE_URL}/signals/active")
if sig_data and isinstance(sig_data, list):
    print(f"  Active Signals   : {len(sig_data)}")
    for s in sig_data:
        print(f"    - {s.get('asset')} {s.get('direction')} @ {s.get('entry_low')}-{s.get('entry_high')}")

print("=" * 60)
print("NOTE: If Analyzer is RUNNING, new signals should appear periodically.")
print("If Active Signals = 0, check market hours or wait for setup.")
print("=" * 60)
