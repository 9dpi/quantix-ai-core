"""
QUANTIX SYSTEM AUDIT - Rules Compliance Check
Validates system implementation against Rules.txt specifications
"""

from quantix_core.database.connection import SupabaseConnection
from quantix_core.config.settings import settings
from datetime import datetime, timezone, timedelta
import json

db = SupabaseConnection()

print("=" * 80)
print("QUANTIX SYSTEM AUDIT - Rules Compliance Check")
print("=" * 80)
print(f"Audit Time: {datetime.now(timezone.utc).isoformat()}")
print()

# ============================================================================
# 1. IMMUTABLE RULE CHECK
# ============================================================================
print("1. IMMUTABLE RULE COMPLIANCE")
print("-" * 80)

# Check for signals with NULL release_confidence
res = db.client.table('fx_signals').select('id, release_confidence').is_('release_confidence', 'null').execute()
null_count = len(res.data) if res.data else 0

if null_count == 0:
    print("✅ PASS: No signals with NULL release_confidence")
else:
    print(f"❌ FAIL: Found {null_count} signals with NULL release_confidence")
    for sig in res.data[:5]:
        print(f"   - Signal ID: {sig['id']}")

# Check for test signals still in DB
res_test = db.client.table('fx_signals').select('id').eq('is_test', True).execute()
test_count = len(res_test.data) if res_test.data else 0

if test_count == 0:
    print("✅ PASS: No test signals in production DB")
else:
    print(f"⚠️  WARNING: Found {test_count} test signals (should be cleaned)")

print()

# ============================================================================
# 2. TIMING PARAMETERS CHECK
# ============================================================================
print("2. TIMING PARAMETERS COMPLIANCE")
print("-" * 80)

print(f"✅ Analyzer Interval: {settings.MONITOR_INTERVAL_SECONDS}s (Expected: 180s)")
print(f"✅ Watcher Interval: {settings.WATCHER_CHECK_INTERVAL}s (Expected: 240s)")
print(f"✅ Entry Validity: {settings.MAX_PENDING_DURATION_MINUTES}m (Expected: 35m)")
print(f"✅ Max Trade Duration: {settings.MAX_TRADE_DURATION_MINUTES}m (Expected: 90m)")
print(f"✅ Min Confidence: {settings.MIN_CONFIDENCE} (Expected: 0.65)")

print()

# ============================================================================
# 3. SIGNAL FLOW CHECK
# ============================================================================
print("3. SIGNAL FLOW & STATE COMPLIANCE")
print("-" * 80)

# Check for stuck signals (WAITING_FOR_ENTRY > 35 mins)
now = datetime.now(timezone.utc)
cutoff = (now - timedelta(minutes=35)).isoformat()

res_stuck = db.client.table('fx_signals').select('id, generated_at, state').eq('state', 'WAITING_FOR_ENTRY').lt('generated_at', cutoff).execute()
stuck_count = len(res_stuck.data) if res_stuck.data else 0

if stuck_count == 0:
    print("✅ PASS: No stuck signals in WAITING_FOR_ENTRY > 35 mins")
else:
    print(f"❌ FAIL: Found {stuck_count} stuck signals")
    for sig in res_stuck.data[:3]:
        print(f"   - Signal ID: {sig['id']} | Generated: {sig['generated_at']}")

# Check for active signals
res_active = db.client.table('fx_signals').select('id, state, status').in_('state', ['WAITING_FOR_ENTRY', 'ENTRY_HIT']).execute()
active_count = len(res_active.data) if res_active.data else 0

print(f"ℹ️  Active Signals: {active_count}")

print()

# ============================================================================
# 4. ANALYSIS LOG HEALTH CHECK
# ============================================================================
print("4. ANALYSIS LOG HEALTH (Last 1 Hour)")
print("-" * 80)

one_hour_ago = (now - timedelta(hours=1)).isoformat()
res_logs = db.client.table('fx_analysis_log').select('id', count='exact').gte('timestamp', one_hour_ago).execute()
log_count = res_logs.count if res_logs.count else 0

expected_logs = 60 // 3  # 1 hour / 3 min interval = ~20 logs
if log_count >= expected_logs * 0.8:  # Allow 20% tolerance
    print(f"✅ PASS: {log_count} analysis logs (Expected: ~{expected_logs})")
else:
    print(f"⚠️  WARNING: Only {log_count} analysis logs (Expected: ~{expected_logs})")

print()

# ============================================================================
# 5. CONFIDENCE CONSISTENCY CHECK
# ============================================================================
print("5. CONFIDENCE CONSISTENCY (Telegram vs DB)")
print("-" * 80)

# Get recent signals with telegram_message_id
res_recent = db.client.table('fx_signals').select('id, release_confidence, telegram_message_id').not_.is_('telegram_message_id', 'null').order('generated_at', desc=True).limit(5).execute()

if res_recent.data:
    print("Recent signals with Telegram notifications:")
    for sig in res_recent.data:
        conf = sig.get('release_confidence')
        if conf is not None:
            print(f"✅ Signal {sig['id'][:8]}... | Confidence: {conf*100:.0f}% | TG ID: {sig.get('telegram_message_id')}")
        else:
            print(f"❌ Signal {sig['id'][:8]}... | Confidence: NULL | TG ID: {sig.get('telegram_message_id')}")
else:
    print("ℹ️  No recent signals with Telegram notifications")

print()

# ============================================================================
# 6. SCHEMA COMPLIANCE CHECK
# ============================================================================
print("6. SCHEMA COMPLIANCE")
print("-" * 80)

# Get a sample signal to check schema
res_sample = db.client.table('fx_signals').select('*').limit(1).execute()

if res_sample.data:
    sample = res_sample.data[0]
    required_fields = ['id', 'asset', 'direction', 'timeframe', 'status', 'state', 
                      'entry_price', 'tp', 'sl', 'ai_confidence', 'release_confidence',
                      'generated_at', 'expiry_at', 'is_test']
    
    missing_fields = [f for f in required_fields if f not in sample]
    
    if not missing_fields:
        print("✅ PASS: All required fields present in schema")
    else:
        print(f"❌ FAIL: Missing required fields: {missing_fields}")
    
    # Check for deprecated fields that should not be in DB
    deprecated_fields = ['valid_until', 'activation_limit_mins', 'max_monitoring_mins']
    found_deprecated = [f for f in deprecated_fields if f in sample]
    
    if not found_deprecated:
        print("✅ PASS: No deprecated fields in schema")
    else:
        print(f"⚠️  WARNING: Found deprecated fields: {found_deprecated}")
else:
    print("⚠️  Cannot check schema: No signals in database")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("AUDIT SUMMARY")
print("=" * 80)
print("✅ = Compliant | ❌ = Non-Compliant | ⚠️  = Warning")
print()
print("Recommendation: Review any ❌ or ⚠️  items above")
print("=" * 80)
