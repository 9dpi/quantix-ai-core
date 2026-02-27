
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def analyze_recent_signals():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    params = {
        "generated_at": f"gte.{cutoff}",
        "order": "generated_at.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        print(f"--- RECENT SIGNALS ANALYSIS (Last 48h) ---")
        print(f"{'Time (UTC)':<20} | {'Asset':<8} | {'Side':<5} | {'State':<15} | {'Result':<15} | {'Price Info'}")
        print("-" * 110)
        
        for s in signals:
            gen_at = str(s.get('generated_at') or 'N/A')[:19]
            asset = str(s.get('asset') or 'N/A')
            side = str(s.get('direction') or 'N/A')
            state = str(s.get('state') or 'N/A')
            result = str(s.get('result') or 'N/A')
            entry = s.get('entry_price')
            tp = s.get('tp')
            sl = s.get('sl')
            
            entry_str = f"{entry:.5f}" if entry is not None else "N/A"
            tp_str = f"{tp:.5f}" if tp is not None else "N/A"
            sl_str = f"{sl:.5f}" if sl is not None else "N/A"
            
            print(f"{gen_at:<20} | {asset:<8} | {side:<5} | {state:<15} | {result:<15} | E:{entry_str} TP:{tp_str} SL:{sl_str}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    analyze_recent_signals()
