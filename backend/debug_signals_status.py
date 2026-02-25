
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_signals():
    today = datetime.now(timezone.utc).date().isoformat()
    params = {
        "generated_at": f"gte.{today}",
        "order": "generated_at.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"Signals for {today}:")
        print("-" * 120)
        print(f"{'Generated At':<25} | {'ID':<38} | {'Asset':<10} | {'Dir':<5} | {'State':<20} | {'Exit Reason':<15}")
        print("-" * 120)
        
        for s in signals:
            gen_at = str(s.get('generated_at') or 'N/A')
            sig_id = str(s.get('id') or 'N/A')
            asset = str(s.get('asset') or 'N/A')
            direction = str(s.get('direction') or 'N/A')
            state = str(s.get('state') or 'N/A')
            result = str(s.get('result') or 'N/A')
            
            print(f"{gen_at[:23]:<25} | {sig_id:<38} | {asset:<10} | {direction:<5} | {state:<20} | {result:<15}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_signals()
