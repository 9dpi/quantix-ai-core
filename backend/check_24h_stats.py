
import requests
import json
from datetime import datetime, timezone, timedelta

URL = "https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals"
HEADERS = {
    "apikey": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"
}

def check_24h_stats():
    twenty_four_hours_ago = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    
    params = {
        "generated_at": f"gte.{twenty_four_hours_ago}",
        "order": "generated_at.desc"
    }
    
    try:
        response = requests.get(URL, headers=HEADERS, params=params)
        response.raise_for_status()
        signals = response.json()
        
        total = len(signals)
        states = {}
        confidences = []
        
        print(f"\n[SUMMARY] SIGNALS IN LAST 24H (Since {twenty_four_hours_ago[:16]})")
        print("=" * 120)
        print(f"{'Generated At':<25} | {'Asset':<10} | {'State':<20} | {'Status':<15} | {'Conf':<6} | {'Result':<10}")
        print("-" * 120)
        
        for s in signals:
            gen_at = str(s.get('generated_at') or 'N/A')
            asset = str(s.get('asset') or 'N/A')
            state = str(s.get('state') or 'N/A')
            status = str(s.get('status') or 'N/A')
            conf = s.get('ai_confidence', 0) or 0
            result = str(s.get('result') or 'N/A')
            
            states[state] = states.get(state, 0) + 1
            confidences.append(float(conf))
            
            print(f"{gen_at[:23]:<25} | {asset:<10} | {state:<20} | {status:<15} | {conf:<6.2f} | {result:<10}")
            
        print("=" * 120)
        print(f"PROCESSED TOTAL: {total}")
        for st, count in states.items():
            print(f"- {st}: {count}")
            
        avg_conf = sum(confidences) / total if total > 0 else 0
        print(f"AVERAGE CONFIDENCE: {avg_conf:.2%}")
        
        # Calculate Win Rate (excluding WAITING/ENTRY_HIT/CANCELLED)
        completed = states.get("TP_HIT", 0) + states.get("SL_HIT", 0)
        if completed > 0:
            win_rate = (states.get("TP_HIT", 0) / completed) * 100
            print(f"WIN RATE (Completed): {win_rate:.1f}% ({states.get('TP_HIT', 0)} wins / {completed} total)")
        else:
            print("WIN RATE: N/A (No completed signals)")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_24h_stats()
