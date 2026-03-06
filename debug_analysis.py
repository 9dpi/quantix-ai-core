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
    print("--- ANALYSIS LOG AUDIT (HIGH CONFIDENCE) ---")
    query_url = f"{URL}/rest/v1/fx_analysis_log?select=timestamp,asset,direction,confidence,status&order=timestamp.desc&limit=50"
    
    try:
        resp = requests.get(query_url, headers=headers)
        if resp.status_code != 200:
            print(f"Error: {resp.status_code} - {resp.text}")
            return
            
        logs = resp.json()
        print(f"{'TIME':<10} | {'ASSET':<12} | {'CONF':<4} | {'STATUS'}")
        print("-" * 55)
        for s in logs:
            ts = s.get("timestamp", "N/A")[11:19]
            asset = s.get("asset", "UNK")
            conf = s.get("confidence", 0) or 0
            status = s.get("status", "NONE")
            
            # Filter for signals-like entries
            if conf > 0.5:
                print(f"{ts:<10} | {asset:12} | {conf*100:3.0f}% | {status[:30]}")
            
    except Exception as e:
        print(f"FAIL: {e}")

if __name__ == "__main__":
    debug()
