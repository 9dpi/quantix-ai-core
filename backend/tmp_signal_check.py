"""
Focused signal diagnostic: Why no signals since last night?
"""
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone, timedelta

def check():
    now = datetime.now(timezone.utc)
    print(f"🕐 UTC: {now.strftime('%Y-%m-%d %H:%M:%S')} | Local (GMT+7): {(now + timedelta(hours=7)).strftime('%H:%M:%S')}")
    print(f"📅 {now.strftime('%A')}")
    print()

    # 1. LAST SIGNALS 
    print("=" * 60)
    print("📊 LAST 10 SIGNALS")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_SIGNALS).select(
            'id,asset,direction,entry_price,sl,tp,ai_confidence,release_confidence,state,generated_at'
        ).order('generated_at', desc=True).limit(10).execute()
        for s in (res.data or []):
            gen = s.get('generated_at', 'N/A')
            print(f"  [{gen[:19]}] {s.get('asset','?')} {s.get('direction','?')} "
                  f"| Conf: {s.get('ai_confidence','?')}/{s.get('release_confidence','?')} "
                  f"| State: {s.get('state','?')}")
    except Exception as e:
        print(f"  ❌ {e}")

    print()

    # 2. ANALYZER HEARTBEAT - Is it alive?
    print("=" * 60)
    print("💓 ANALYZER HEARTBEAT (last 5)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,status'
        ).eq('asset', 'HEARTBEAT_ANALYZER').order('timestamp', desc=True).limit(5).execute()
        for h in (res.data or []):
            ts = h.get('timestamp', '')
            hb_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age_min = (now - hb_time).total_seconds() / 60
            print(f"  [{ts[:19]}] {h.get('status','')} ({age_min:.0f}m ago)")
        
        if res.data:
            latest = datetime.fromisoformat(res.data[0]['timestamp'].replace("Z", "+00:00"))
            gap = (now - latest).total_seconds() / 60
            if gap > 5:
                print(f"\n  ⚠️ ANALYZER MAY BE DOWN! Last heartbeat was {gap:.0f} minutes ago!")
            else:
                print(f"\n  ✅ Analyzer is ALIVE (last heartbeat {gap:.1f}m ago)")
    except Exception as e:
        print(f"  ❌ {e}")

    print()

    # 3. WATCHER HEARTBEAT
    print("=" * 60)
    print("👁️ WATCHER HEARTBEAT (last 5)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,status'
        ).eq('asset', 'HEARTBEAT_WATCHER').order('timestamp', desc=True).limit(5).execute()
        for h in (res.data or []):
            ts = h.get('timestamp', '')
            hb_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            age_min = (now - hb_time).total_seconds() / 60
            print(f"  [{ts[:19]}] {h.get('status','')} ({age_min:.0f}m ago)")
    except Exception as e:
        print(f"  ❌ {e}")

    print()

    # 4. ANALYZED entries (actual market analysis with confidence scores)
    print("=" * 60)
    print("🧠 LAST 15 ANALYSIS RESULTS (market scans with confidence)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,asset,direction,confidence,price,status'
        ).eq('status', 'ANALYZED').order('timestamp', desc=True).limit(15).execute()
        for a in (res.data or []):
            ts = a.get('timestamp', '')[:19]
            conf = a.get('confidence', 0)
            direction = a.get('direction', '?')
            price = a.get('price', 0)
            threshold = settings.MIN_CONFIDENCE
            marker = "🟢 RELEASE" if conf >= threshold else "🔴 BELOW"
            print(f"  [{ts}] {direction:4s} | Conf: {conf:.2f} ({marker} ≥{threshold}) | Price: {price}")
        
        if not res.data:
            print("  ⚠️ NO ANALYZED entries found! Analyzer may not be reaching analysis stage.")
    except Exception as e:
        print(f"  ❌ {e}")

    print()

    # 5. REJECTION reasons (Birth vs Skip)
    print("=" * 60)
    print("🔍 RECENT ANALYZER LOGS (all types, last 30)")
    print("=" * 60)
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG).select(
            'timestamp,asset,status'
        ).eq('asset', 'ANALYZER_LOG').order('timestamp', desc=True).limit(30).execute()
        for l in (res.data or []):
            ts = l.get('timestamp', '')[:19]
            status = l.get('status', '')
            # Truncate but show key parts
            if len(status) > 200:
                status = status[:200] + "..."
            print(f"  [{ts}] {status}")
    except Exception as e:
        print(f"  ❌ {e}")

    print()

    # 6. Check market hours
    print("=" * 60)
    print("⏰ MARKET HOURS CHECK")
    print("=" * 60)
    try:
        from quantix_core.utils.market_hours import MarketHours
        should_trade = MarketHours.should_generate_signals()
        print(f"  MarketHours.should_generate_signals() = {should_trade}")
        if not should_trade:
            print("  ⚠️ MARKET IS CLOSED according to MarketHours! This blocks ALL signal generation.")
    except Exception as e:
        print(f"  ❌ {e}")

    # 7. Settings summary
    print()
    print("=" * 60)
    print("⚙️ KEY SETTINGS")
    print("=" * 60)
    print(f"  MIN_CONFIDENCE: {settings.MIN_CONFIDENCE}")
    print(f"  TP_PIPS: {settings.TP_PIPS}")
    print(f"  SL_PIPS: {settings.SL_PIPS}")
    print(f"  MAX_SIGNALS_PER_DAY: {settings.MAX_SIGNALS_PER_DAY}")
    print(f"  MIN_RELEASE_INTERVAL: {settings.MIN_RELEASE_INTERVAL_MINUTES}m")
    print(f"  MONITOR_INTERVAL: {settings.MONITOR_INTERVAL_SECONDS}s")

if __name__ == '__main__':
    check()
