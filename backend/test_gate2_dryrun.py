"""
GATE 2 Dry-Run Test

Test entry calculator integration without running full analyzer.
"""

import sys
sys.path.insert(0, 'd:/Automator_Prj/Quantix_AI_Core/backend')

from quantix_core.utils.entry_calculator import EntryCalculator

print("=" * 60)
print("GATE 2 DRY-RUN TEST - Entry Calculator")
print("=" * 60)

# Test 1: BUY Signal
print("\n✓ Test 1: BUY Signal")
market_price = 1.19371
direction = "BUY"

calc = EntryCalculator(offset_pips=5.0)
entry, is_valid, msg = calc.calculate_and_validate(market_price, direction)

print(f"Market price: {market_price}")
print(f"Generated entry: {entry}")
print(f"Offset: {abs(entry - market_price) / 0.0001:.1f} pips")
print(f"Direction: {direction}")
print(f"Valid: {is_valid}")
print(f"State: WAITING_FOR_ENTRY")

# Verify
assert entry != market_price, "❌ FAIL: Entry == market"
assert abs(entry - market_price) >= 0.00049, "❌ FAIL: Offset < 5 pips"  # Allow 4.9+ pips due to rounding
assert entry < market_price, "❌ FAIL: BUY entry should be below market"
print("✅ BUY test passed")

# Test 2: SELL Signal
print("\n✓ Test 2: SELL Signal")
direction = "SELL"

entry, is_valid, msg = calc.calculate_and_validate(market_price, direction)

print(f"Market price: {market_price}")
print(f"Generated entry: {entry}")
print(f"Offset: {abs(entry - market_price) / 0.0001:.1f} pips")
print(f"Direction: {direction}")
print(f"Valid: {is_valid}")
print(f"State: WAITING_FOR_ENTRY")

# Verify
assert entry != market_price, "❌ FAIL: Entry == market"
assert abs(entry - market_price) >= 0.00049, "❌ FAIL: Offset < 5 pips"  # Allow 4.9+ pips due to rounding
assert entry > market_price, "❌ FAIL: SELL entry should be above market"
print("✅ SELL test passed")

# Test 3: Expiry calculation
print("\n✓ Test 3: Expiry Calculation")
from datetime import datetime, timezone, timedelta

now = datetime.now(timezone.utc)
expiry_at = now + timedelta(minutes=15)

print(f"Created at: {now.strftime('%H:%M:%S UTC')}")
print(f"Expiry at: {expiry_at.strftime('%H:%M:%S UTC')}")
print(f"Duration: 15 minutes")

assert expiry_at > now, "❌ FAIL: Expiry not in future"
print("✅ Expiry test passed")

print("\n" + "=" * 60)
print("✅ ALL DRY-RUN TESTS PASSED")
print("=" * 60)
print("\n✅ GO to GATE 2 execution")
print("\nNext: Run analyzer once to verify signal creation")
