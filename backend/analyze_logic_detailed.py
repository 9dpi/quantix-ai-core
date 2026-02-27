
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def analyze_logic():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=8)).isoformat()
    params = {
        "timestamp": f"gte.{cutoff}",
        "direction": "in.(BUY,SELL)",
        "order": "timestamp.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"--- DETAILED ANALYSIS LOGS (Last 8h) ---")
        print(f"{'Time (UTC)':<20} | {'Dir':<5} | {'Raw':<5} | {'Release':<7} | {'Refinement'}")
        print("-" * 120)
        
        for l in logs:
            gen_at = l.get('timestamp')[:19]
            direction = l.get('direction')
            raw = l.get('confidence') or 0
            rel = l.get('release_confidence') or 0
            ref = l.get('refinement') or 'N/A'
            
            print(f"{gen_at:<20} | {direction:<5} | {raw:.2f} | {rel:.2f} | {ref}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_logic()
