
import requests
import json
from datetime import datetime, timezone, timedelta

URL_SIGNALS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
URL_ANALYSIS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_analysis():
    # Check for the specific timestamp the user mentioned
    target_ts = "2026-02-05T14:49:12.990909+00:00"
    params = {
        "timestamp": f"eq.{target_ts}"
    }
    
    print(f"Checking Analysis Log for timestamp: {target_ts}")
    try:
        response = requests.get(URL_ANALYSIS, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data:
            for item in data:
                print(json.dumps(item, indent=2))
                release_conf = item.get('release_confidence', 0)
                refinement = item.get('refinement', 'N/A')
                print(f"\nRelease Confidence: {release_conf}")
                print(f"Refinement: {refinement}")
        else:
            print("No entry found for this exact timestamp in DB.")
            
    except Exception as e:
        print(f"Error checking analysis: {e}")

def check_active_signals_at_time():
    # Check signals that were active (WAITING or ENTRY_HIT) around 14:49 UTC
    # Since we don't have a perfect "active_at" query, we'll check all signals generated today
    # and look for their lifecycle.
    today = "2026-02-05"
    params = {
        "generated_at": f"gte.{today}T00:00:00",
        "order": "generated_at.asc"
    }
    
    print(f"\nChecking signals generated on {today}:")
    try:
        response = requests.get(URL_SIGNALS, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"{'Gen At':<25} | {'ID':<38} | {'State':<20} | {'TG ID':<15}")
        for s in signals:
            gen_at = s.get('generated_at', 'N/A')
            sig_id = s.get('id', 'N/A')
            state = s.get('state', 'N/A')
            tg_id = s.get('telegram_message_id', 'N/A')
            print(f"{gen_at[:23]:<25} | {sig_id:<38} | {state:<20} | {tg_id}")
            
    except Exception as e:
        print(f"Error checking signals: {e}")

if __name__ == "__main__":
    check_analysis()
    check_active_signals_at_time()
