
import requests
import json
from datetime import datetime, timezone

URL_ANALYSIS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_analysis():
    params = {
        "order": "timestamp.desc",
        "limit": 50
    }
    
    try:
        response = requests.get(URL_ANALYSIS, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        found_watcher = False
        print(f"{'Timestamp':<25} | {'Asset':<20} | {'Status':<30}")
        print("-" * 80)
        
        for l in logs:
            ts = str(l.get('timestamp') or 'N/A')
            asset = str(l.get('asset') or 'N/A')
            status = str(l.get('status') or 'N/A')
            
            if asset == "HEARTBEAT_WATCHER":
                found_watcher = True
                print(f"{ts[:23]:<25} | {asset:<20} | {status:<30}")
            
        if not found_watcher:
            print("No HEARTBEAT_WATCHER found in last 50 logs.")
            
    except Exception as e:
        print(f"Error checking analysis: {e}")

if __name__ == "__main__":
    check_analysis()
