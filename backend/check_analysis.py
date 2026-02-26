
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
        "limit": 10
    }
    
    try:
        response = requests.get(URL_ANALYSIS, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"{'Timestamp':<25} | {'Asset':<10} | {'Status':<15} | {'Price':<10} | {'Direction':<10} | {'Conf':<6}")
        print("-" * 100)
        
        for l in logs:
            ts = str(l.get('timestamp') or 'N/A')
            asset = str(l.get('asset') or 'N/A')
            status = str(l.get('status') or 'N/A')
            price = str(l.get('price') or 'N/A')
            direction = str(l.get('direction') or 'N/A')
            conf = str(l.get('confidence') or 'N/A')
            
            print(f"{ts[:23]:<25} | {asset:<10} | {status:<15} | {price:<10} | {direction:<10} | {conf:<6}")
            
    except Exception as e:
        print(f"Error checking analysis: {e}")

if __name__ == "__main__":
    check_analysis()
