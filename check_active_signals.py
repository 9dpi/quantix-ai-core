import sys
sys.path.insert(0, 'backend')

from quantix_core.database.connection import get_supabase_client

# Get Supabase client
sb = get_supabase_client()

# Check for active signals
print("=== Checking Active Signals ===")
result = sb.table('fx_signals')\
    .select('*')\
    .not_.is_('telegram_message_id', 'null')\
    .in_('state', ['WAITING_FOR_ENTRY', 'ENTRY_HIT'])\
    .order('generated_at', desc=True)\
    .limit(1)\
    .execute()

if result.data:
    signal = result.data[0]
    print(f"✅ Found active signal:")
    print(f"   ID: {signal['id']}")
    print(f"   Direction: {signal['direction']}")
    print(f"   Entry: {signal['entry_price']}")
    print(f"   TP: {signal['take_profit']}")
    print(f"   SL: {signal['stop_loss']}")
    print(f"   State: {signal['state']}")
    print(f"   Telegram ID: {signal['telegram_message_id']}")
else:
    print("❌ No active signals found")

# Check total signals with telegram_message_id
print("\n=== Checking All Released Signals ===")
result_all = sb.table('fx_signals')\
    .select('*', count='exact')\
    .not_.is_('telegram_message_id', 'null')\
    .order('generated_at', desc=True)\
    .limit(10)\
    .execute()

print(f"Total released signals: {result_all.count}")
if result_all.data:
    print(f"\nLast 10 signals:")
    for sig in result_all.data:
        print(f"  - ID {sig['id']}: {sig['direction']} | State: {sig['state']} | Generated: {sig['generated_at']}")
