
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals?order=generated_at.desc&limit=1"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_logs():
    LOG_URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log?asset=in.(SYSTEM_API,SYSTEM_WEB,LAUNCHER,CRASH)&order=timestamp.desc&limit=20"
    try:
        response = requests.get(LOG_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        print(f"{'Time':<25} | {'Asset':<12} | {'Direction':<10} | {'Status'}")
        print("-" * 100)
        for log in data:
            print(f"{log['timestamp'][:23]:<25} | {log['asset']:<12} | {log['direction']:<10} | {log['status']}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_logs()
