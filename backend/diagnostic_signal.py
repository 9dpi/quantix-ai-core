
import requests
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals?id=eq.693507fd-0f02-4822-b806-49b8b187ad8f"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_specific():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        print(f"Current Data for 693507fd: {json.dumps(data, indent=2)}")
        
        # Try to update it
        print("\nAttempting to close it...")
        payload = {
            "state": "CANCELLED",
            "status": "CLOSED_TIMEOUT",
            "result": "CANCELLED",
            "closed_at": datetime.now(timezone.utc).isoformat()
        }
        res = requests.patch(URL, headers=HEADERS, json=payload)
        print(f"Patch Status: {res.status_code}")
        print(f"Patch Response: {res.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_specific()
