
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def analyze_closed():
    # Last 3 days
    cutoff = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    params = {
        "generated_at": f"gte.{cutoff}",
        "state": "eq.CLOSED",
        "order": "generated_at.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"--- RECENT CLOSED SIGNALS ---")
        if not signals:
            print("No closed signals in the last 3 days.")
            return

        for s in signals:
            print(f"ID: {s.get('id')[:8]} | Result: {s.get('result'):<10} | Stats: Entry:{s.get('entry_price')} TP:{s.get('tp')} SL:{s.get('sl')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_closed()
