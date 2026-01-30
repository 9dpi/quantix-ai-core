"""
Unit Tests for Signal Watcher

Tests touch detection logic and state transition methods.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock
from quantix_core.engine.signal_watcher import SignalWatcher


class TestTouchDetection:
    """Test touch detection methods"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.watcher = SignalWatcher(
            supabase_client=Mock(),
            td_client=Mock(),
            check_interval=60
        )
    
    # ========================================
    # ENTRY TOUCH TESTS
    # ========================================
    
    def test_buy_entry_touched_by_low(self):
        """BUY entry touched when candle low reaches entry"""
        signal = {
            "direction": "BUY",
            "entry_price": 1.19321
        }
        candle = {
            "low": 1.19320,   # Touched!
            "high": 1.19400
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is True
    
    def test_buy_entry_not_touched(self):
        """BUY entry not touched when price stays above"""
        signal = {
            "direction": "BUY",
            "entry_price": 1.19321
        }
        candle = {
            "low": 1.19350,   # Above entry
            "high": 1.19400
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is False
    
    def test_sell_entry_touched_by_high(self):
        """SELL entry touched when candle high reaches entry"""
        signal = {
            "direction": "SELL",
            "entry_price": 1.19421
        }
        candle = {
            "low": 1.19350,
            "high": 1.19425   # Touched!
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is True
    
    def test_sell_entry_not_touched(self):
        """SELL entry not touched when price stays below"""
        signal = {
            "direction": "SELL",
            "entry_price": 1.19421
        }
        candle = {
            "low": 1.19350,
            "high": 1.19400   # Below entry
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is False
    
    # ========================================
    # TP TOUCH TESTS
    # ========================================
    
    def test_buy_tp_touched_by_high(self):
        """BUY TP touched when candle high reaches TP"""
        signal = {
            "direction": "BUY",
            "tp": 1.19421
        }
        candle = {
            "low": 1.19350,
            "high": 1.19425   # Touched TP!
        }
        
        assert self.watcher.is_tp_touched(signal, candle) is True
    
    def test_buy_tp_not_touched(self):
        """BUY TP not touched when price stays below"""
        signal = {
            "direction": "BUY",
            "tp": 1.19421
        }
        candle = {
            "low": 1.19350,
            "high": 1.19400   # Below TP
        }
        
        assert self.watcher.is_tp_touched(signal, candle) is False
    
    def test_sell_tp_touched_by_low(self):
        """SELL TP touched when candle low reaches TP"""
        signal = {
            "direction": "SELL",
            "tp": 1.19321
        }
        candle = {
            "low": 1.19320,   # Touched TP!
            "high": 1.19400
        }
        
        assert self.watcher.is_tp_touched(signal, candle) is True
    
    def test_sell_tp_not_touched(self):
        """SELL TP not touched when price stays above"""
        signal = {
            "direction": "SELL",
            "tp": 1.19321
        }
        candle = {
            "low": 1.19350,   # Above TP
            "high": 1.19400
        }
        
        assert self.watcher.is_tp_touched(signal, candle) is False
    
    # ========================================
    # SL TOUCH TESTS
    # ========================================
    
    def test_buy_sl_touched_by_low(self):
        """BUY SL touched when candle low reaches SL"""
        signal = {
            "direction": "BUY",
            "sl": 1.19221
        }
        candle = {
            "low": 1.19220,   # Touched SL!
            "high": 1.19350
        }
        
        assert self.watcher.is_sl_touched(signal, candle) is True
    
    def test_buy_sl_not_touched(self):
        """BUY SL not touched when price stays above"""
        signal = {
            "direction": "BUY",
            "sl": 1.19221
        }
        candle = {
            "low": 1.19250,   # Above SL
            "high": 1.19350
        }
        
        assert self.watcher.is_sl_touched(signal, candle) is False
    
    def test_sell_sl_touched_by_high(self):
        """SELL SL touched when candle high reaches SL"""
        signal = {
            "direction": "SELL",
            "sl": 1.19521
        }
        candle = {
            "low": 1.19400,
            "high": 1.19525   # Touched SL!
        }
        
        assert self.watcher.is_sl_touched(signal, candle) is True
    
    def test_sell_sl_not_touched(self):
        """SELL SL not touched when price stays below"""
        signal = {
            "direction": "SELL",
            "sl": 1.19521
        }
        candle = {
            "low": 1.19400,
            "high": 1.19500   # Below SL
        }
        
        assert self.watcher.is_sl_touched(signal, candle) is False
    
    # ========================================
    # EDGE CASES
    # ========================================
    
    def test_entry_touched_exact_match(self):
        """Entry touched when price exactly equals entry"""
        signal = {
            "direction": "BUY",
            "entry_price": 1.19321
        }
        candle = {
            "low": 1.19321,   # Exact match
            "high": 1.19400
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is True
    
    def test_missing_entry_price(self):
        """Handle missing entry price gracefully"""
        signal = {
            "direction": "BUY"
            # No entry_price
        }
        candle = {
            "low": 1.19320,
            "high": 1.19400
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is False
    
    def test_missing_direction(self):
        """Handle missing direction gracefully"""
        signal = {
            "entry_price": 1.19321
            # No direction
        }
        candle = {
            "low": 1.19320,
            "high": 1.19400
        }
        
        assert self.watcher.is_entry_touched(signal, candle) is False


class TestStateTransitions:
    """Test state transition logic"""
    
    def setup_method(self):
        """Setup test fixtures with mocked database"""
        self.mock_db = Mock()
        self.mock_table = Mock()
        self.mock_update = Mock()
        self.mock_eq = Mock()
        
        # Setup mock chain: db.table().update().eq().execute()
        self.mock_db.table.return_value = self.mock_table
        self.mock_table.update.return_value = self.mock_update
        self.mock_update.eq.return_value = self.mock_eq
        self.mock_eq.execute.return_value = None
        
        self.watcher = SignalWatcher(
            supabase_client=self.mock_db,
            td_client=Mock(),
            check_interval=60
        )
    
    def test_transition_to_entry_hit(self):
        """Test WAITING_FOR_ENTRY → ENTRY_HIT transition"""
        signal = {"id": "test-123"}
        candle = {"timestamp": "2026-01-30T15:45:00Z"}
        
        self.watcher.transition_to_entry_hit(signal, candle)
        
        # Verify database update was called
        self.mock_table.update.assert_called_once_with({
            "state": "ENTRY_HIT",
            "entry_hit_at": "2026-01-30T15:45:00Z"
        })
        self.mock_update.eq.assert_called_once_with("id", "test-123")
    
    def test_transition_to_tp_hit(self):
        """Test ENTRY_HIT → TP_HIT transition"""
        signal = {"id": "test-456"}
        candle = {"timestamp": "2026-01-30T16:00:00Z"}
        
        self.watcher.transition_to_tp_hit(signal, candle)
        
        # Verify database update
        self.mock_table.update.assert_called_once_with({
            "state": "TP_HIT",
            "result": "PROFIT",
            "closed_at": "2026-01-30T16:00:00Z"
        })
        self.mock_update.eq.assert_called_once_with("id", "test-456")
    
    def test_transition_to_sl_hit(self):
        """Test ENTRY_HIT → SL_HIT transition"""
        signal = {"id": "test-789"}
        candle = {"timestamp": "2026-01-30T16:15:00Z"}
        
        self.watcher.transition_to_sl_hit(signal, candle)
        
        # Verify database update
        self.mock_table.update.assert_called_once_with({
            "state": "SL_HIT",
            "result": "LOSS",
            "closed_at": "2026-01-30T16:15:00Z"
        })
        self.mock_update.eq.assert_called_once_with("id", "test-789")
    
    def test_transition_to_cancelled(self):
        """Test WAITING_FOR_ENTRY → CANCELLED transition"""
        signal = {"id": "test-999"}
        
        self.watcher.transition_to_cancelled(signal)
        
        # Verify database update (closed_at will be current time)
        update_call = self.mock_table.update.call_args[0][0]
        assert update_call["state"] == "CANCELLED"
        assert update_call["result"] == "CANCELLED"
        assert "closed_at" in update_call
        
        self.mock_update.eq.assert_called_once_with("id", "test-999")


class TestRealWorldScenarios:
    """Test real-world signal lifecycle scenarios"""
    
    def setup_method(self):
        """Setup watcher with mocks"""
        self.watcher = SignalWatcher(
            supabase_client=Mock(),
            td_client=Mock(),
            check_interval=60
        )
    
    def test_buy_signal_full_lifecycle_tp(self):
        """Test complete BUY signal lifecycle ending in TP"""
        
        # Signal waiting for entry
        signal = {
            "id": "buy-001",
            "direction": "BUY",
            "entry_price": 1.19321,
            "tp": 1.19421,
            "sl": 1.19221
        }
        
        # Candle 1: Entry touched
        candle1 = {"low": 1.19320, "high": 1.19350}
        assert self.watcher.is_entry_touched(signal, candle1) is True
        
        # Now signal is in ENTRY_HIT state
        signal["state"] = "ENTRY_HIT"
        
        # Candle 2: TP touched
        candle2 = {"low": 1.19350, "high": 1.19425}
        assert self.watcher.is_tp_touched(signal, candle2) is True
        
        # Signal should end in TP_HIT state
    
    def test_sell_signal_full_lifecycle_sl(self):
        """Test complete SELL signal lifecycle ending in SL"""
        
        # Signal waiting for entry
        signal = {
            "id": "sell-001",
            "direction": "SELL",
            "entry_price": 1.19421,
            "tp": 1.19321,
            "sl": 1.19521
        }
        
        # Candle 1: Entry touched
        candle1 = {"low": 1.19400, "high": 1.19425}
        assert self.watcher.is_entry_touched(signal, candle1) is True
        
        # Now signal is in ENTRY_HIT state
        signal["state"] = "ENTRY_HIT"
        
        # Candle 2: SL touched (price went against us)
        candle2 = {"low": 1.19450, "high": 1.19525}
        assert self.watcher.is_sl_touched(signal, candle2) is True
        
        # Signal should end in SL_HIT state
    
    def test_signal_expires_without_entry(self):
        """Test signal expiring before entry is touched"""
        
        signal = {
            "id": "exp-001",
            "state": "WAITING_FOR_ENTRY",
            "direction": "BUY",
            "entry_price": 1.19321,
            "expiry_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
        }
        
        # Entry never touched, and expiry time has passed
        candle = {"low": 1.19350, "high": 1.19400}
        
        assert self.watcher.is_entry_touched(signal, candle) is False
        
        # Signal should be cancelled
