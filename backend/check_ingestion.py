
import requests
import json
from datetime import datetime, timezone

URL_SIGNALS = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
URL_INGESTION = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/ingestion_audit_log"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_ingestion():
    params = {
        "order": "created_at.desc",
        "limit": 5
    }
    
    try:
        response = requests.get(URL_INGESTION, headers=HEADERS, params=params)
        response.raise_for_status()
        logs = response.json()
        
        print(f"{'Created At':<25} | {'Asset':<10} | {'Status':<15} | {'Total Rows':<10}")
        print("-" * 70)
        
        for l in logs:
            created_at = str(l.get('created_at') or 'N/A')
            asset = str(l.get('asset') or 'N/A')
            status = str(l.get('status') or 'N/A')
            total = str(l.get('total_rows') or 'N/A')
            
            print(f"{created_at[:23]:<25} | {asset:<10} | {status:<15} | {total:<10}")
            
    except Exception as e:
        print(f"Error checking ingestion: {e}")

if __name__ == "__main__":
    check_ingestion()
