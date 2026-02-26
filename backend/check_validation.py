
import requests
import json
from datetime import datetime, timezone

URL_VALIDATION = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signal_validation"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_validation():
    params = {
        "order": "created_at.desc",
        "limit": 5
    }
    
    try:
        response = requests.get(URL_VALIDATION, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"{'Created At':<25} | {'Asset':<10} | {'Status':<15} | {'Score':<6}")
        print("-" * 70)
        
        for s in signals:
            ca = str(s.get('created_at') or 'N/A')
            asset = str(s.get('asset') or 'N/A')
            status = str(s.get('status') or 'N/A')
            score = str(s.get('validation_score') or 'N/A')
            
            print(f"{ca[:23]:<25} | {asset:<10} | {status:<15} | {score:<6}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_validation()
