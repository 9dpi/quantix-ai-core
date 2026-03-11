"""
Deep diagnostic: Check why no signals are being generated.
Checks:
1. Latest signals from fx_signals table
2. Recent analyzer logs (ALL, not just keyword-filtered)
3. Circuit breaker state
4. Last health report
"""
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone, timedelta
import json

def deep_diagnose():
    now = datetime.now(timezone.utc)
    print(f"🕐 Current UTC time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 Day of week: {now.strftime('%A')}")
    print()

    # 1. Recent signals
    print("=" * 60)
    print("📊 LAST 10 SIGNALS (fx_signals)")
    print("=" * 60)
    try:
        res = db.client.table('fx_signals').select(
            'id,pair,direction,entry_price,sl,tp,confidence,state,generated_at,sent_at'
        ).order('generated_at', desc=True).limit(10).execute()
        signals = res.data or []
        if not signals:
            print("⚠️ NO SIGNALS FOUND IN DATABASE!")
        for s in signals:
            gen = s.get('generated_at', 'N/A')
            print(f"  [{gen}] {s.get('pair','?')} {s.get('direction','?')} | "
                  f"Conf: {s.get('confidence','?')} | State: {s.get('state','?')} | "
                  f"Entry: {s.get('entry_price','?')} SL: {s.get('sl','?')} TP: {s.get('tp','?')}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

    # 2. Recent analyzer logs (raw, last 50)
    print("=" * 60)
    print("📋 LAST 50 ANALYZER LOGS (fx_analysis_log)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,asset,status,confidence,direction'
        ).order('timestamp', desc=True).limit(50).execute()
        logs = res.data or []
        if not logs:
            print("⚠️ NO ANALYZER LOGS FOUND!")
        
        # Group by type
        analyzer_logs = []
        signal_logs = []
        other_logs = []
        
        for l in logs:
            asset = l.get('asset', '')
            if asset == 'ANALYZER_LOG':
                analyzer_logs.append(l)
            elif 'SIGNAL' in asset.upper():
                signal_logs.append(l)
            else:
                other_logs.append(l)
        
        print(f"\n  📌 Analyzer Logs: {len(analyzer_logs)}")
        for l in analyzer_logs[:20]:
            ts = l.get('timestamp', '')
            status = l.get('status', '')[:250]
            print(f"    [{ts[11:19]}] {status}")
        
        print(f"\n  📌 Signal Logs: {len(signal_logs)}")
        for l in signal_logs[:10]:
            ts = l.get('timestamp', '')
            status = l.get('status', '')[:250]
            conf = l.get('confidence', 'N/A')
            direction = l.get('direction', 'N/A')
            print(f"    [{ts[11:19]}] {l.get('asset','')} | Conf: {conf} | Dir: {direction} | {status[:150]}")
        
        print(f"\n  📌 Other Logs: {len(other_logs)}")
        for l in other_logs[:10]:
            ts = l.get('timestamp', '')
            asset = l.get('asset', '')
            status = l.get('status', '')[:150]
            print(f"    [{ts[11:19]}] {asset} | {status}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

    # 3. Check signal lifecycle
    print("=" * 60)
    print("🔄 SIGNAL LIFECYCLE (last 10 entries)")
    print("=" * 60)
    try:
        res = db.client.table('fx_signal_lifecycle').select('*').order('timestamp', desc=True).limit(10).execute()
        lifecycles = res.data or []
        if not lifecycles:
            print("⚠️ NO LIFECYCLE ENTRIES FOUND!")
        for lc in lifecycles:
            ts = lc.get('timestamp', '')
            sig_id = str(lc.get('signal_id', ''))[:8]
            old = lc.get('old_state', '?')
            new = lc.get('new_state', '?')
            reason = lc.get('reason', '')[:100]
            print(f"  [{ts[11:19]}] Signal {sig_id} | {old} → {new} | {reason}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()

    # 4. Look for specific rejection reasons in last 200 analyzer logs
    print("=" * 60)
    print("🔍 REJECTION/SKIP ANALYSIS (last 200 logs)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,status'
        ).eq('asset', 'ANALYZER_LOG').order('timestamp', desc=True).limit(200).execute()
        logs = res.data or []
        
        keywords = {
            "SKIP": 0, "sideways": 0, "ANTI-BURST": 0, "threshold": 0, 
            "below": 0, "reject": 0, "cooldown": 0, "circuit": 0,
            "Birth": 0, "SIGNAL_RELEASED": 0, "confidence": 0,
            "error": 0, "fail": 0, "timeout": 0
        }
        
        for l in logs:
            status = l.get('status', '')
            for k in keywords:
                if k.lower() in status.lower():
                    keywords[k] += 1
        
        print("  Keyword frequency in last 200 analyzer logs:")
        for k, v in sorted(keywords.items(), key=lambda x: x[1], reverse=True):
            if v > 0:
                print(f"    {k}: {v}")
        
        # Show last timestamp range
        if logs:
            newest = logs[0].get('timestamp', 'N/A')
            oldest = logs[-1].get('timestamp', 'N/A')
            print(f"\n  Time range: {oldest} → {newest}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == '__main__':
    deep_diagnose()
