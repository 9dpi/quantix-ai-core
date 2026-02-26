
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_history():
    params = {
        "order": "generated_at.desc",
        "limit": 10
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"{'Generated At':<25} | {'Asset':<10} | {'State':<20} | {'Status':<15} | {'Result':<15}")
        print("-" * 100)
        
        for s in signals:
            gen_at = str(s.get('generated_at') or 'N/A')
            asset = str(s.get('asset') or 'N/A')
            state = str(s.get('state') or 'N/A')
            status = str(s.get('status') or 'N/A')
            result = str(s.get('result') or 'N/A')
            
            print(f"{gen_at[:23]:<25} | {asset:<10} | {state:<20} | {status:<15} | {result:<15}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_history()
