
import requests
import json
import os
import sys
from datetime import datetime, timezone, timedelta

# Configuration
URL_SIGNALS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
HEADERS = {
    "apikey": API_KEY,
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def get_stuck_signals():
    """Find signals that are blocking the pipeline."""
    # Logic: WAITING_FOR_ENTRY > 30m or ENTRY_HIT > 90m
    now = datetime.now(timezone.utc)
    stuck_ids = []
    
    try:
        # Fetch all active signals
        params = {"state": "in.(WAITING_FOR_ENTRY,ENTRY_HIT)"}
        response = requests.get(URL_SIGNALS, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        for s in signals:
            sig_id = s.get('id')
            state = s.get('state')
            gen_at_str = s.get('generated_at')
            
            if not gen_at_str: continue
            gen_at = datetime.fromisoformat(gen_at_str.replace('Z', '+00:00'))
            age_mins = (now - gen_at).total_seconds() / 60
            
            is_stuck = False
            reason = ""
            if state == "WAITING_FOR_ENTRY" and age_mins > 35:
                is_stuck = True
                reason = f"Pending > 35m ({age_mins:.1f}m)"
            elif state == "ENTRY_HIT" and age_mins > 35:
                is_stuck = True
                reason = f"Active > 35m ({age_mins:.1f}m)"
                
            if is_stuck:
                stuck_ids.append({"id": sig_id, "reason": reason, "asset": s.get('asset')})
                
        return stuck_ids
    except Exception as e:
        print(f"Error fetching signals: {e}")
        return []

def clear_signal(sig_id):
    """Force close a specific signal."""
    url = f"{URL_SIGNALS}?id=eq.{sig_id}"
    data = {
        "state": "CANCELLED",
        "status": "EXPIRED",
        "result": "CANCELLED",
        "closed_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        response = requests.patch(url, headers=HEADERS, json=data)
        return response.status_code < 400
    except:
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear-all":
        stuck = get_stuck_signals()
        if not stuck:
            print("No stuck signals found.")
        else:
            print(f"Found {len(stuck)} stuck signals. Clearing...")
            for s in stuck:
                success = clear_signal(s['id'])
                status = "DONE" if success else "FAILED"
                print(f"  - {s['asset']} ({s['id']}): {status}")
    else:
        # Default: list only
        stuck = get_stuck_signals()
        if not stuck:
            print("CLEAN")
        else:
            for s in stuck:
                print(f"STUCK|{s['id']}|{s['asset']}|{s['reason']}")
