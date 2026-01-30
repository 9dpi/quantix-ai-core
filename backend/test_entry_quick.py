"""
Quick Test Script for Entry Calculator
Run this to verify the entry price generator works correctly
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from quantix_core.utils.entry_calculator import EntryCalculator

def test_basic_functionality():
    """Test basic entry calculation"""
    print("=" * 60)
    print("TESTING ENTRY PRICE CALCULATOR")
    print("=" * 60)
    
    calc = EntryCalculator(offset_pips=5.0)
    market_price = 1.19371
    
    # Test 1: BUY Signal
    print("\n📊 Test 1: BUY Signal")
    print(f"Market Price: {market_price}")
    
    entry_buy, valid_buy, msg_buy = calc.calculate_and_validate(market_price, "BUY")
    print(f"Entry Price: {entry_buy}")
    print(f"Valid: {valid_buy}")
    print(f"Message: {msg_buy}")
    print(f"Distance: {abs(entry_buy - market_price):.5f} ({abs(entry_buy - market_price) / 0.0001:.1f} pips)")
    
    assert entry_buy == 1.19321, f"Expected 1.19321, got {entry_buy}"
    assert valid_buy is True, f"Expected valid=True, got {valid_buy}"
    print("✅ BUY test passed!")
    
    # Test 2: SELL Signal
    print("\n📊 Test 2: SELL Signal")
    print(f"Market Price: {market_price}")
    
    entry_sell, valid_sell, msg_sell = calc.calculate_and_validate(market_price, "SELL")
    print(f"Entry Price: {entry_sell}")
    print(f"Valid: {valid_sell}")
    print(f"Message: {msg_sell}")
    print(f"Distance: {abs(entry_sell - market_price):.5f} ({abs(entry_sell - market_price) / 0.0001:.1f} pips)")
    
    assert entry_sell == 1.19421, f"Expected 1.19421, got {entry_sell}"
    assert valid_sell is True, f"Expected valid=True, got {valid_sell}"
    print("✅ SELL test passed!")
    
    # Test 3: TP/SL Calculation from Entry
    print("\n📊 Test 3: TP/SL Calculation (BUY)")
    tp_buy = round(entry_buy + 0.0010, 5)
    sl_buy = round(entry_buy - 0.0010, 5)
    print(f"Entry: {entry_buy}")
    print(f"TP: {tp_buy} (+10 pips)")
    print(f"SL: {sl_buy} (-10 pips)")
    
    assert tp_buy == 1.19421, f"Expected TP=1.19421, got {tp_buy}"
    assert sl_buy == 1.19221, f"Expected SL=1.19221, got {sl_buy}"
    print("✅ TP/SL calculation passed!")
    
    # Test 4: Validation - Entry too close
    print("\n📊 Test 4: Validation - Entry too close")
    entry_close = 1.19370  # Only 0.1 pips away
    valid_close, msg_close = calc.validate_entry_price(entry_close, market_price, "BUY")
    print(f"Entry: {entry_close}")
    print(f"Valid: {valid_close}")
    print(f"Message: {msg_close}")
    
    assert valid_close is False, "Expected validation to fail for entry too close"
    print("✅ Validation test passed!")
    
    # Test 5: Validation - Wrong direction
    print("\n📊 Test 5: Validation - Wrong direction")
    entry_wrong = 1.19400  # Above market for BUY (wrong!)
    valid_wrong, msg_wrong = calc.validate_entry_price(entry_wrong, market_price, "BUY")
    print(f"Entry: {entry_wrong} (above market)")
    print(f"Direction: BUY")
    print(f"Valid: {valid_wrong}")
    print(f"Message: {msg_wrong}")
    
    assert valid_wrong is False, "Expected validation to fail for wrong direction"
    print("✅ Direction validation passed!")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
    print("\n📊 Summary:")
    print(f"  - BUY entry: {entry_buy} (5 pips below market)")
    print(f"  - SELL entry: {entry_sell} (5 pips above market)")
    print(f"  - Validation: Working correctly")
    print(f"  - TP/SL calculation: Correct")
    print("\n🎯 Entry Price Generator is ready for integration!")

if __name__ == "__main__":
    try:
        test_basic_functionality()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
