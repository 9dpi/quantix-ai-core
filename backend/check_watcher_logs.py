import requests, json

URL = 'https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_analysis_log'
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk'
}

params = {'order': 'timestamp.desc', 'limit': 20, 'asset': 'eq.HEARTBEAT_WATCHER'}
r = requests.get(URL, headers=HEADERS, params=params)

if r.status_code == 200:
    for log in r.json():
        print(f"[{log['timestamp'][:19]}] {log['asset']} | Status: {log['status']}")
else:
    print(f"Error: {r.status_code} - {r.text}")
