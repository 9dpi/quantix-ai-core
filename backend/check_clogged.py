
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_clogged():
    # Only WAITING_FOR_ENTRY or ENTRY_HIT
    states = ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
    
    print(f"Checking for signals in states: {states}")
    print("-" * 150)
    print(f"{'Generated At':<25} | {'ID':<38} | {'Asset':<10} | {'State':<20} | {'Hit At':<25} | {'Status':<10} | {'Entry':<10} | {'TP':<10} | {'SL':<10}")
    print("-" * 170)
    
    found_any = False
    for state in states:
        params = {
            "state": f"eq.{state}",
            "order": "generated_at.desc"
        }
        
        try:
            response = requests.get(URL, headers=HEADERS, params=params)
            response.raise_for_status()
            signals = response.json()
            
            for s in signals:
                found_any = True
                gen_at = str(s.get('generated_at') or 'N/A')
                sig_id = str(s.get('id') or 'N/A')
                asset = str(s.get('asset') or 'N/A')
                state_str = str(s.get('state') or 'N/A')
                hit_at = str(s.get('entry_hit_at') or 'N/A')
                status = str(s.get('status') or 'N/A')
                entry = str(s.get('entry_price') or 'N/A')
                tp = str(s.get('tp') or 'N/A')
                sl = str(s.get('sl') or 'N/A')
                
                print(f"{gen_at[:23]:<25} | {sig_id:<38} | {asset:<10} | {state_str:<20} | {hit_at[:23]:<25} | {status:<10} | {entry:<10} | {tp:<10} | {sl:<10}")
                
        except Exception as e:
            print(f"Error for state {state}: {e}")
            
    if not found_any:
        print("No active signals found.")

if __name__ == "__main__":
    check_clogged()
