"""
Unit Tests for Entry Price Calculator

Tests the entry price calculation and validation logic for v2 Future Entry signals.
"""

import pytest
from quantix_core.utils.entry_calculator import EntryCalculator, calculate_entry_price, validate_entry_price


class TestEntryCalculator:
    """Test suite for EntryCalculator class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.calc = EntryCalculator(offset_pips=5.0)
        self.market_price = 1.19371
    
    # ============================================
    # CALCULATION TESTS
    # ============================================
    
    def test_buy_entry_below_market(self):
        """BUY entry must be below market price"""
        entry = self.calc.calculate_entry_price(self.market_price, "BUY")
        
        assert entry < self.market_price
        assert entry == 1.19321  # 5 pips below
    
    def test_sell_entry_above_market(self):
        """SELL entry must be above market price"""
        entry = self.calc.calculate_entry_price(self.market_price, "SELL")
        
        assert entry > self.market_price
        assert entry == 1.19421  # 5 pips above
    
    def test_entry_precision(self):
        """Entry should be rounded to 5 decimal places"""
        entry = self.calc.calculate_entry_price(1.193714567, "BUY")
        
        # Should round to 5 decimals
        assert len(str(entry).split('.')[-1]) <= 5
    
    def test_custom_offset(self):
        """Should accept custom offset"""
        custom_offset = 0.0010  # 10 pips
        entry = self.calc.calculate_entry_price(
            self.market_price, 
            "BUY", 
            custom_offset=custom_offset
        )
        
        assert entry == 1.19271  # 10 pips below
    
    def test_invalid_direction(self):
        """Should raise ValueError for invalid direction"""
        with pytest.raises(ValueError, match="Invalid direction"):
            self.calc.calculate_entry_price(self.market_price, "INVALID")
    
    # ============================================
    # VALIDATION TESTS
    # ============================================
    
    def test_valid_buy_entry(self):
        """Valid BUY entry should pass validation"""
        entry = 1.19321  # 5 pips below market
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is True
        assert msg == "Valid"
    
    def test_valid_sell_entry(self):
        """Valid SELL entry should pass validation"""
        entry = 1.19421  # 5 pips above market
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "SELL"
        )
        
        assert is_valid is True
        assert msg == "Valid"
    
    def test_entry_too_close_to_market(self):
        """Entry too close to market should fail validation"""
        entry = 1.19370  # Only 0.1 pips away
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is False
        assert "too close" in msg.lower()
    
    def test_buy_entry_above_market_invalid(self):
        """BUY entry above market should fail validation"""
        entry = 1.19400  # Above market
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is False
        assert "must be below" in msg.lower()
    
    def test_sell_entry_below_market_invalid(self):
        """SELL entry below market should fail validation"""
        entry = 1.19300  # Below market
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "SELL"
        )
        
        assert is_valid is False
        assert "must be above" in msg.lower()
    
    def test_entry_too_far_from_market(self):
        """Entry too far from market should fail validation"""
        entry = 1.18371  # 100 pips away (exceeds max 50 pips)
        is_valid, msg = self.calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is False
        assert "too far" in msg.lower()
    
    # ============================================
    # COMBINED CALCULATION + VALIDATION TESTS
    # ============================================
    
    def test_calculate_and_validate_buy(self):
        """Test combined calculation and validation for BUY"""
        entry, is_valid, msg = self.calc.calculate_and_validate(
            self.market_price, 
            "BUY"
        )
        
        assert entry == 1.19321
        assert is_valid is True
        assert msg == "Valid"
    
    def test_calculate_and_validate_sell(self):
        """Test combined calculation and validation for SELL"""
        entry, is_valid, msg = self.calc.calculate_and_validate(
            self.market_price, 
            "SELL"
        )
        
        assert entry == 1.19421
        assert is_valid is True
        assert msg == "Valid"
    
    def test_calculate_and_validate_invalid_direction(self):
        """Test combined function with invalid direction"""
        entry, is_valid, msg = self.calc.calculate_and_validate(
            self.market_price, 
            "INVALID"
        )
        
        assert entry == 0.0
        assert is_valid is False
        assert "Invalid direction" in msg
    
    # ============================================
    # EDGE CASE TESTS
    # ============================================
    
    def test_zero_market_price(self):
        """Should handle zero market price gracefully"""
        entry = self.calc.calculate_entry_price(0.0, "BUY")
        assert entry == -0.0005  # 5 pips below zero
    
    def test_very_small_market_price(self):
        """Should handle very small prices"""
        entry = self.calc.calculate_entry_price(0.00001, "BUY")
        assert entry < 0.00001
    
    def test_very_large_market_price(self):
        """Should handle very large prices"""
        entry = self.calc.calculate_entry_price(100.0, "BUY")
        assert entry == 99.9995  # 5 pips below
    
    # ============================================
    # CONFIGURATION TESTS
    # ============================================
    
    def test_custom_min_distance(self):
        """Test custom minimum distance configuration"""
        calc = EntryCalculator(
            offset_pips=5.0,
            min_distance_pips=10.0  # Require 10 pips minimum
        )
        
        entry = 1.19321  # Only 5 pips away
        is_valid, msg = calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is False  # Should fail (< 10 pips)
    
    def test_custom_max_distance(self):
        """Test custom maximum distance configuration"""
        calc = EntryCalculator(
            offset_pips=5.0,
            max_distance_pips=3.0  # Only allow 3 pips max
        )
        
        entry = 1.19321  # 5 pips away
        is_valid, msg = calc.validate_entry_price(
            entry, 
            self.market_price, 
            "BUY"
        )
        
        assert is_valid is False  # Should fail (> 3 pips)


class TestConvenienceFunctions:
    """Test convenience functions for backward compatibility"""
    
    def test_calculate_entry_price_function(self):
        """Test standalone calculate_entry_price function"""
        entry = calculate_entry_price(1.19371, "BUY", offset=0.0005)
        assert entry == 1.19321
    
    def test_validate_entry_price_function(self):
        """Test standalone validate_entry_price function"""
        is_valid, msg = validate_entry_price(1.19321, 1.19371, "BUY")
        assert is_valid is True
        assert msg == "Valid"


# ============================================
# INTEGRATION TESTS
# ============================================

class TestRealWorldScenarios:
    """Test real-world scenarios"""
    
    def test_typical_eurusd_buy_signal(self):
        """Test typical EURUSD BUY signal"""
        calc = EntryCalculator(offset_pips=5.0)
        market_price = 1.19371
        
        entry, is_valid, msg = calc.calculate_and_validate(market_price, "BUY")
        
        assert entry == 1.19321
        assert is_valid is True
        
        # Verify TP/SL can be calculated from entry
        tp = entry + 0.0010  # 10 pips TP
        sl = entry - 0.0010  # 10 pips SL
        
        assert tp == 1.19421
        assert sl == 1.19221
    
    def test_typical_eurusd_sell_signal(self):
        """Test typical EURUSD SELL signal"""
        calc = EntryCalculator(offset_pips=5.0)
        market_price = 1.19371
        
        entry, is_valid, msg = calc.calculate_and_validate(market_price, "SELL")
        
        assert entry == 1.19421
        assert is_valid is True
        
        # Verify TP/SL can be calculated from entry
        tp = entry - 0.0010  # 10 pips TP
        sl = entry + 0.0010  # 10 pips SL
        
        assert tp == 1.19321
        assert sl == 1.19521
    
    def test_multiple_signals_same_market_price(self):
        """Test that multiple signals at same market price get same entry"""
        calc = EntryCalculator(offset_pips=5.0)
        market_price = 1.19371
        
        entry1, _, _ = calc.calculate_and_validate(market_price, "BUY")
        entry2, _, _ = calc.calculate_and_validate(market_price, "BUY")
        
        assert entry1 == entry2  # Should be deterministic
