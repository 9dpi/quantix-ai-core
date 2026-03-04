import requests, json
import sys

URL = 'https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log'
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk'
}

asset = sys.argv[1] if len(sys.argv) > 1 else 'HEARTBEAT_WATCHER'
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

params = {'order': 'timestamp.desc', 'limit': limit, 'asset': f'eq.{asset}'}
r = requests.get(URL, headers=HEADERS, params=params)

if r.status_code == 200:
    data = r.json()
    if not data:
        print(f"No logs found for {asset}")
    for log in data:
        print(f"[{log['timestamp'][:19]}] {log['asset']} | Status: {log['status']}")
else:
    print(f"Error: {r.status_code} - {r.text}")
