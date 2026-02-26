
import requests
import json
from datetime import datetime, timezone

URL_ANALYSIS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_launchers():
    params = {
        "status": "eq.LAUNCHING",
        "order": "timestamp.desc",
        "limit": 10
    }
    
    try:
        response = requests.get(URL_ANALYSIS, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"{'Timestamp':<25} | {'Asset':<20} | {'Status':<30}")
        print("-" * 80)
        
        for l in logs:
            ts = str(l.get('timestamp') or 'N/A')
            asset = str(l.get('asset') or 'N/A')
            status = str(l.get('status') or 'N/A')
            print(f"{ts[:23]:<25} | {asset:<20} | {status:<30}")
            
    except Exception as e:
        print(f"Error checking launchers: {e}")

if __name__ == "__main__":
    check_launchers()
