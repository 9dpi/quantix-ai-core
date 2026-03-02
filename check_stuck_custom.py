
import requests
import json
import sys
from datetime import datetime, timezone, timedelta

# Set encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_stuck_signals():
    # Only check statuses that might be stuck
    stuck_statuses = ['WAITING_FOR_ENTRY', 'ACTIVE', 'PENDING', 'GENERATED']
    
    print(f"Checking for signals with statuses: {stuck_statuses}...")
    
    params = {
        "state": f"in.({','.join(stuck_statuses)})",
        "order": "generated_at.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        if not signals:
            print("[OK] No potentially stuck signals found.")
        else:
            print(f"[!] Found {len(signals)} potentially stuck signals:")
            for s in signals:
                print(f" - ID: {s['id']} | Asset: {s['asset']} | State: {s['state']} | Created: {s['generated_at']}")
            
    except Exception as e:
        print(f"Error checking signals: {e}")

def check_recent_analysis():
    print("\nChecking recent system heartbeats...")
    URL_ANALYSIS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
    params = {
        "limit": 5,
        "order": "created_at.desc"
    }
    try:
        response = requests.get(URL_ANALYSIS, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        for l in logs:
            print(f" - [{l['created_at']}] {l['service_name']} | {l['event_type']} | {l.get('message', '')}")
    except Exception as e:
        print(f"Error checking analysis logs: {e}")

if __name__ == "__main__":
    check_stuck_signals()
    check_recent_analysis()
