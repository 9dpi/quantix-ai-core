
import requests
import json
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Load env variables manually
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

SUBAPASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

if not SUBAPASE_URL or not SUPABASE_KEY:
    print("❌ Critical: Missing Supabase credentials in .env")
    exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

REST_URL = f"{SUBAPASE_URL}/rest/v1/fx_signals"

def nuke_zombies():
    print("🚀 STARTING PRODUCTION RECOVERY (FINAL ATTEMPT - STANDARD VALUES)...")
    
    # 1. Clear Stuck Published/EntryHit signals
    print("\nStep 1: Clearing stuck active signals...")
    res = requests.get(
        REST_URL, 
        headers=HEADERS, 
        params={"status": "in.(PUBLISHED,ENTRY_HIT)", "select": "id"}
    )
    
    if res.status_code == 200:
        stuck = res.json()
        if stuck:
            for sig in stuck:
                print(f"  - Expiring: {sig['id']}")
                patch_res = requests.patch(
                    REST_URL,
                    headers=HEADERS,
                    params={"id": f"eq.{sig['id']}"},
                    json={
                        "state": "EXPIRED",
                        "status": "CLOSED",
                        "result": "CANCELLED",
                        "closed_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                print(f"    Result: {patch_res.status_code}")
        else:
            print("  - No stuck active signals found.")

    # 2. Nuke Zombies
    print("\nStep 2: Nuking zombies...")
    res = requests.get(
        REST_URL, 
        headers=HEADERS, 
        params={
            "state": "eq.WAITING_FOR_ENTRY", 
            "telegram_message_id": "is.null",
            "select": "id"
        }
    )
    
    if res.status_code == 200:
        zombies = res.json()
        if zombies:
            zombie_ids = [z['id'] for z in zombies]
            print(f"  - Found {len(zombie_ids)} zombies.")
            
            for i in range(0, len(zombie_ids), 50):
                batch = zombie_ids[i:i + 50]
                ids_str = ",".join(batch)
                patch_res = requests.patch(
                    REST_URL,
                    headers=HEADERS,
                    params={"id": f"in.({ids_str})"},
                    json={
                        "state": "CANCELLED",
                        "status": "CLOSED",
                        "result": "CANCELLED",
                        "closed_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                if patch_res.status_code in [200, 201, 204]:
                    print(f"    ✅ Batch Done.")
                else:
                    print(f"    ❌ Batch Failed: {patch_res.text}")
        else:
            print("  - No zombies found.")

    print("\n🏁 RECOVERY COMPLETE.")

if __name__ == "__main__":
    nuke_zombies()
