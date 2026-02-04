import requests
import json
import sys
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load env variables
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

SUBAPASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUBAPASE_URL or not SUPABASE_KEY:
    print("❌ Mission Supabase credentials")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

REST_URL = f"{SUBAPASE_URL}/rest/v1/fx_signals"

def get_status():
    print("\n🔍 SYSTEM STATUS CHECK")
    print("-" * 30)
    res = requests.get(REST_URL, headers=HEADERS, params={"state": "in.(WAITING_FOR_ENTRY,ENTRY_HIT,PREPARED)", "select": "id,state,asset,generated_at"})
    if res.status_code == 200:
        signals = res.json()
        if not signals:
            print("✅ No active signals. System is UNLOCKED.")
        else:
            for s in signals:
                print(f"  - [{s['state']}] {s['id']} | {s['asset']} | Generated: {s['generated_at']}")
    else:
        print(f"❌ Failed to fetch status: {res.text}")

def unblock_global_lock():
    print("\n🔓 UNBLOCKING GLOBAL LOCK (Force Closing Active Signals)")
    res = requests.get(REST_URL, headers=HEADERS, params={"state": "in.(WAITING_FOR_ENTRY,ENTRY_HIT)", "select": "id"})
    if res.status_code == 200:
        signals = res.json()
        if not signals:
            print("  - No active signals to clear.")
            return
        
        ids = [s['id'] for s in signals]
        print(f"  - Closing {len(ids)} active signals...")
        patch_res = requests.patch(
            REST_URL,
            headers=HEADERS,
            params={"id": f"in.({','.join(ids)})"},
            json={
                "state": "CANCELLED",
                "status": "CLOSED",
                "result": "CANCELLED",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        if patch_res.status_code in [200, 204]:
            print("  ✅ SUCCESS: Global Lock cleared.")
        else:
            print(f"  ❌ FAILED: {patch_res.text}")

def nuke_prepared_zombies():
    print("\n🧹 NUKING PREPARED ZOMBIES (Phase 1 Leftovers)")
    res = requests.get(REST_URL, headers=HEADERS, params={"state": "eq.PREPARED", "select": "id"})
    if res.status_code == 200:
        signals = res.json()
        if not signals:
            print("  - No prepared zombies found.")
            return
        
        ids = [s['id'] for s in signals]
        print(f"  - Removing {len(ids)} prepared entries...")
        patch_res = requests.patch(
            REST_URL,
            headers=HEADERS,
            params={"id": f"in.({','.join(ids)})"},
            json={
                "state": "CANCELLED",
                "status": "CLOSED",
                "result": "CANCELLED",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        if patch_res.status_code in [200, 204]:
            print("  ✅ SUCCESS: Prepared zombies nuked.")
        else:
            print(f"  ❌ FAILED: {patch_res.text}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        get_status()
    elif sys.argv[1] == "status":
        get_status()
    elif sys.argv[1] == "unblock":
        unblock_global_lock()
    elif sys.argv[1] == "nuke":
        nuke_prepared_zombies()
    elif sys.argv[1] == "all":
        unblock_global_lock()
        nuke_prepared_zombies()
