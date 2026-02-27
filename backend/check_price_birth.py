
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_price_at_birth():
    params = {
        "timestamp": "gte.2026-02-27T14:40:00Z",
        "order": "timestamp.asc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"--- PRICE LOGS AROUND SIGNAL BIRTH ---")
        for l in logs:
            print(f"{l.get('timestamp')[:19]} | Price: {l.get('price'):.5f} | Status: {l.get('status')} | Dir: {l.get('direction')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_price_at_birth()
