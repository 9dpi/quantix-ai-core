
import urllib.request
import json
from datetime import datetime, timezone

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals?generated_at=gte.{}&order=generated_at.desc"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
AUTH = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"

def check_signals():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = URL.format(today)
    
    req = urllib.request.Request(url)
    req.add_header("apikey", API_KEY)
    req.add_header("Authorization", AUTH)
    
    try:
        with urllib.request.urlopen(req) as response:
            signals = json.loads(response.read().decode())
            
            print(f"Signals for {today}:")
            print("-" * 120)
            print(f"{'Generated At':<25} | {'ID':<38} | {'Asset':<10} | {'Dir':<5} | {'State':<20} | {'Exit Reason':<15}")
            print("-" * 120)
            
            for s in signals:
                gen_at = s.get('generated_at', 'N/A')
                sig_id = s.get('id', 'N/A')
                asset = s.get('asset', 'N/A')
                direction = s.get('direction', 'N/A')
                state = s.get('state', 'N/A')
                result = s.get('result', 'N/A')
                
                print(f"{gen_at[:23]:<25} | {sig_id:<38} | {asset:<10} | {direction:<5} | {state:<20} | {str(result):<15}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_signals()
