import os
import sys
import requests
import json

# Manual Supabase Fetch
URL = "https://wttsaprezgvircanthbk.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk"

headers = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json"
}

def debug():
    print("--- DEEP SIGNAL RELEASE AUDIT ---")
    query_url = f"{URL}/rest/v1/fx_signals?select=generated_at,asset,direction,state,status,ai_confidence,release_confidence,telegram_message_id,explainability&order=generated_at.desc&limit=10"
    
    try:
        resp = requests.get(query_url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
            return
            
        signals = resp.json()
        print(f"{'TIME':<10} | {'ASSET':<8} | {'DIR':<4} | {'STATE':<12} | {'AI':<4} | {'REL':<4} | {'SENT'}")
        print("-" * 65)
        for s in signals:
            gen_at = s.get("generated_at", "N/A")[11:19]
            asset = s.get("asset", "UNK")
            direction = s.get("direction", "???")
            state = s.get("state") or s.get("status") or "UNKNOWN"
            ai_conf = s.get("ai_confidence", 0) or 0
            rel_conf = s.get("release_confidence", 0) or 0
            tg_id = s.get("telegram_message_id")
            explain = s.get("explainability", "NONE")
            
            sent_status = "YES" if tg_id else "NO"
            
            print(f"{gen_at:<10} | {asset:8} | {direction:4} | {state:12} | {ai_conf*100:3.0f}% | {rel_conf*100:3.0f}% | {sent_status}")
            if not tg_id:
                print(f"   Explain: {str(explain)[:120]}...")
            print("-" * 65)
            
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    debug()
