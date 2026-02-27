
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_heartbeats():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat()
    params = {
        "timestamp": f"gte.{cutoff}",
        "order": "timestamp.desc",
        "limit": 10
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"--- HEARTBEAT ANALYSIS (Last 8h) ---")
        if not logs:
            print("❌ NO HEARTBEATS FOUND in the last 8 hours! The system might be down.")
            return

        for l in logs:
            print(f"{l.get('timestamp')[:19]} | {l.get('asset'):<15} | {l.get('status')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_heartbeats()
