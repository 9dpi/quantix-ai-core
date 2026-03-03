import requests, json

URL = 'https://wttsaprezgvircanthbk.supabase.co/rest/v1/fx_signals'
HEADERS = {
    'apikey': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0dHNhcHJlemd2aXJjYW50aGJrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODM2ODA3MCwiZXhwIjoyMDgzOTQ0MDcwfQ.QGewz8bDfBC6vJce6g4-sHA164bL1y0u71d6HH7PYVk'
}

params = {'order': 'generated_at.desc', 'limit': 10, 
          'select': 'id,direction,state,status,result,entry_price,tp,sl,generated_at,entry_hit_at,closed_at,telegram_message_id,ai_confidence,release_confidence'}
r = requests.get(URL, headers=HEADERS, params=params)

print("=" * 120)
print("SIGNAL LIFECYCLE AUDIT - Last 10 Signals")
print("=" * 120)

for i, s in enumerate(r.json()):
    sid = s['id'][:8]
    gen = str(s.get('generated_at', ''))[:19]
    hit = str(s.get('entry_hit_at') or '')[:19]
    closed = str(s.get('closed_at') or '')[:19]
    
    print(f"\n--- Signal #{i+1}: {sid}... ---")
    print(f"  Direction: {s['direction']} | Entry: {s['entry_price']} | TP: {s['tp']} | SL: {s['sl']}")
    print(f"  State: {s['state']} | Status: {s['status']} | Result: {s.get('result')}")
    print(f"  AI Conf: {s['ai_confidence']} | Release Conf: {s.get('release_confidence')}")
    print(f"  Generated: {gen} | Entry Hit: {hit or 'N/A'} | Closed: {closed or 'N/A'}")
    print(f"  Telegram ID: {s.get('telegram_message_id', 'N/A')}")
    
    # Lifecycle validation
    issues = []
    state = s['state']
    status = s['status']
    result = s.get('result')
    
    # Check 1: Terminal states must have closed_at
    if state in ['TP_HIT', 'SL_HIT', 'CANCELLED'] and not s.get('closed_at'):
        issues.append("❌ Terminal state without closed_at!")
    
    # Check 2: ENTRY_HIT must have entry_hit_at
    if state == 'ENTRY_HIT' and not s.get('entry_hit_at'):
        issues.append("❌ ENTRY_HIT without entry_hit_at!")
    
    # Check 3: TP_HIT should have result=PROFIT
    if state == 'TP_HIT' and result != 'PROFIT':
        issues.append(f"❌ TP_HIT but result={result} (expected PROFIT)")
    
    # Check 4: SL_HIT should have result=LOSS
    if state == 'SL_HIT' and result != 'LOSS':
        issues.append(f"❌ SL_HIT but result={result} (expected LOSS)")
    
    # Check 5: CANCELLED should have result=CANCELLED or EXPIRED
    if state == 'CANCELLED' and result not in ['CANCELLED', 'EXPIRED', 'CLOSED_TIMEOUT']:
        issues.append(f"⚠️ CANCELLED but result={result}")
    
    # Check 6: Telegram ID should exist for published signals
    if not s.get('telegram_message_id'):
        issues.append("⚠️ No Telegram message ID")
    
    # Check 7: TP/SL sanity (BUY: TP > Entry > SL)
    entry = s['entry_price']
    tp = s['tp']
    sl = s['sl']
    if s['direction'] == 'BUY':
        if tp <= entry: issues.append(f"❌ BUY but TP({tp}) <= Entry({entry})")
        if sl >= entry: issues.append(f"❌ BUY but SL({sl}) >= Entry({entry})")
    else:
        if tp >= entry: issues.append(f"❌ SELL but TP({tp}) >= Entry({entry})")
        if sl <= entry: issues.append(f"❌ SELL but SL({sl}) <= Entry({entry})")
    
    if issues:
        print(f"  🚨 ISSUES FOUND:")
        for iss in issues:
            print(f"     {iss}")
    else:
        print(f"  ✅ Lifecycle OK")

print("\n" + "=" * 120)
