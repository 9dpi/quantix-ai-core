
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_web_logs():
    params = {
        "order": "timestamp.desc",
        "limit": 50
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"Recent Logs:")
        print("-" * 100)
        print(f"{'Timestamp':<25} | {'Asset':<15} | {'Status':<40} | {'Direction':<10}")
        print("-" * 100)
        
        for l in logs:
            ts = str(l.get('timestamp') or 'N/A')
            asset = str(l.get('asset') or 'N/A')
            status = str(l.get('status') or 'N/A')
            direction = str(l.get('direction') or 'N/A')
            print(f"{ts[11:19]} | {asset:10} | {direction:10} | {status[:60]}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_web_logs()
