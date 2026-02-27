
import requests, json

URL = 'https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals'
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk'
}

params = {'order': 'generated_at.desc', 'limit': 100}
r = requests.get(URL, headers=HEADERS, params=params)
signals = r.json()

stats = {'total': 0, 'PROFIT': 0, 'LOSS': 0, 'CANCELLED': 0, 'TIMEOUT': 0, 'OTHER': 0, 'entry_never_hit': 0}

for s in signals:
    stats['total'] += 1
    result = s.get('result') or 'NONE'
    state = s.get('state') or 'NONE'

    if result == 'PROFIT':
        stats['PROFIT'] += 1
    elif result == 'LOSS':
        stats['LOSS'] += 1
    elif result == 'CANCELLED' or state == 'CANCELLED':
        stats['CANCELLED'] += 1
        if s.get('entry_hit_at') is None:
            stats['entry_never_hit'] += 1
    elif result == 'TIMEOUT' or state == 'CLOSED':
        stats['TIMEOUT'] += 1
    else:
        stats['OTHER'] += 1

    # Detailed print
    print(f"{s.get('generated_at','')[:19]:20s} | {s.get('direction',''):5s} | State:{s.get('state',''):18s} | Result:{result:12s} | Entry:{s.get('entry_price','N/A')} TP:{s.get('tp','N/A')} SL:{s.get('sl','N/A')}")

print()
print('=' * 60)
print('SIGNAL PERFORMANCE SUMMARY (Last 100)')
print('=' * 60)
for k, v in stats.items():
    print(f'  {k}: {v}')

traded = stats['PROFIT'] + stats['LOSS']
if traded > 0:
    wr = stats['PROFIT'] / traded * 100
    print(f'\n  Win Rate (PROFIT/LOSS only): {wr:.1f}%')
    print(f'  Traded Signals: {traded}')
    print(f'  Cancelled (Never Reached Entry): {stats["entry_never_hit"]}')
