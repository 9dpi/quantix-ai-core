
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals?id=eq.26086fd5-d963-491e-909b-ff97108d93c2"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
AUTH = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"

def force_close():
    data = {
        "state": "CANCELLED",
        "status": "EXPIRED",
        "result": "CANCELLED",
        "closed_at": datetime.now(timezone.utc).isoformat()
    }
    
    headers = {
        "apikey": API_KEY,
        "Authorization": AUTH,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    try:
        response = requests.patch(URL, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code >= 400:
            print(f"Error Body: {response.text}")
        else:
            print("✅ Signal successfully force-closed.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    force_close()
