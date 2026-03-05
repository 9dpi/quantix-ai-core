"""Analyze why entries are not being hit."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import requests
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

# Also fetch signals that were TP/SL to compare
res_expired = db.client.table(settings.TABLE_SIGNALS).select("*").eq("status", "EXPIRED").order("generated_at", desc=True).limit(30).execute()
res_hit = db.client.table(settings.TABLE_SIGNALS).select("*").in_("status", ["CLOSED_TP", "CLOSED_SL"]).order("generated_at", desc=True).limit(20).execute()

expired = res_expired.data or []
hit_signals = res_hit.data or []

print("=" * 90)
print("ENTRY MISS ANALYSIS")
print("=" * 90)

# Analyze EXPIRED signals
entry_gaps = []
for sig in expired:
    entry = sig.get("entry_price", 0)
    gen_at_str = sig.get("generated_at", "")
    direction = sig.get("direction", "BUY")
    tp = sig.get("tp", 0)
    conf = sig.get("release_confidence") or sig.get("ai_confidence") or 0
    
    if not entry or not gen_at_str:
        continue
    
    # Fetch the actual market price AT the time of signal generation
    gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
    start_ms = int(gen_at.timestamp() * 1000)
    
    try:
        resp = requests.get("https://api.binance.com/api/v3/klines", params={
            "symbol": "EURUSDT", "interval": "1m", "startTime": start_ms, "limit": 1
        }, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                market_price = float(data[0][4])  # Close price at that minute
                
                if direction == "BUY":
                    gap = (market_price - entry) * 10000
                else:
                    gap = (entry - market_price) * 10000
                
                tp_pips = abs(tp - entry) * 10000
                entry_type = "MARKET" if abs(gap) < 0.5 else "PENDING"
                
                entry_gaps.append({
                    "id": sig.get("id", "")[:8],
                    "direction": direction,
                    "market": market_price,
                    "entry": entry,
                    "gap": gap,
                    "tp_pips": tp_pips,
                    "conf": conf,
                    "type": entry_type,
                    "time": gen_at.strftime("%m-%d %H:%M")
                })
    except:
        pass

# EXPIRED signals analysis
print(f"\n--- EXPIRED Signals ({len(entry_gaps)} analyzed) ---")
print(f"{'ID':>8} | {'Dir':>4} | {'Market':>10} | {'Entry':>10} | {'Gap':>8} | {'TP':>6} | {'Conf':>5} | {'Type':>7} | Time")
print("-" * 90)

for g in entry_gaps:
    print(f"{g['id']:>8} | {g['direction']:>4} | {g['market']:>10.5f} | {g['entry']:>10.5f} | {g['gap']:>+7.1f}p | {g['tp_pips']:>5.1f}p | {g['conf']:>4.0%} | {g['type']:>7} | {g['time']}")

if entry_gaps:
    avg_gap = sum(abs(g['gap']) for g in entry_gaps) / len(entry_gaps)
    pending = [g for g in entry_gaps if g['type'] == 'PENDING']
    market = [g for g in entry_gaps if g['type'] == 'MARKET']
    
    print(f"\nAVERAGE GAP: {avg_gap:.1f} pips")
    print(f"PENDING entries: {len(pending)} ({len(pending)/len(entry_gaps)*100:.0f}%)")
    print(f"MARKET entries: {len(market)} ({len(market)/len(entry_gaps)*100:.0f}%)")
    
    if pending:
        avg_pending_gap = sum(abs(g['gap']) for g in pending) / len(pending)
        print(f"AVG PENDING GAP: {avg_pending_gap:.1f} pips")

# HIT signals analysis (for comparison)
print(f"\n--- HIT Signals (TP/SL) for comparison ---")  
hit_gaps = []
for sig in hit_signals:
    entry = sig.get("entry_price", 0)
    hit_at = sig.get("entry_hit_at") or sig.get("generated_at", "")
    direction = sig.get("direction", "BUY")
    
    if not entry or not hit_at:
        continue
    
    gen_at_str = sig.get("generated_at", "")
    if not gen_at_str: continue
    gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
    start_ms = int(gen_at.timestamp() * 1000)
    
    try:
        resp = requests.get("https://api.binance.com/api/v3/klines", params={
            "symbol": "EURUSDT", "interval": "1m", "startTime": start_ms, "limit": 1
        }, timeout=5)
        
        if resp.status_code == 200:
            data = resp.json()
            if data:
                market_price = float(data[0][4])
                if direction == "BUY":
                    gap = (market_price - entry) * 10000
                else:
                    gap = (entry - market_price) * 10000
                hit_gaps.append(abs(gap))
    except:
        pass

if hit_gaps:
    print(f"Average entry gap for WINNING signals: {sum(hit_gaps)/len(hit_gaps):.1f} pips")

print("\n" + "=" * 90)
print("ROOT CAUSE DIAGNOSIS:")
print("=" * 90)
if entry_gaps:
    avg_gap = sum(abs(g['gap']) for g in entry_gaps) / len(entry_gaps)
    pending_pct = len([g for g in entry_gaps if g['type'] == 'PENDING']) / len(entry_gaps) * 100
    
    if avg_gap > 2:
        print(f"[!] ENTRY TOO FAR: Average gap is {avg_gap:.1f} pips")
        print(f"    FVG offset (1.5 pips) + market movement = entry unreachable in 35m")
        print(f"    FIX: Reduce FVG offset OR use more MARKET EXECUTION signals")
    if pending_pct > 60:
        print(f"[!] TOO MANY PENDING: {pending_pct:.0f}% are pending orders")
        print(f"    Only ULTRA signals (>=95% conf) get market execution")
        print(f"    FIX: Lower market execution threshold to >=85% confidence")
