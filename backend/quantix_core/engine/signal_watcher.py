"""
Signal Watcher - Monitors active signals and executes state transitions

This module watches signals in WAITING_FOR_ENTRY and ENTRY_HIT states,
detects when price touches entry/TP/SL levels, and performs atomic state transitions.
"""

import time
from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger
from supabase import Client


class SignalWatcher:
    """
    Watches active signals and performs state transitions based on market data.
    
    Responsibilities:
    - Monitor signals in WAITING_FOR_ENTRY and ENTRY_HIT states
    - Fetch latest market candle data
    - Detect entry/TP/SL touches
    - Execute atomic state transitions
    - Send Telegram notifications (delegated to telegram module)
    """
    
    def __init__(
        self,
        supabase_client: Client,
        td_client,
        check_interval: int = 60,
        telegram_notifier=None
    ):
        """
        Initialize signal watcher.
        
        Args:
            supabase_client: Supabase database client
            td_client: TwelveData API client for market data
            check_interval: Seconds between checks (default 60)
            telegram_notifier: Optional Telegram notification handler
        """
        self.db = supabase_client
        self.td_client = td_client
        self.check_interval = check_interval
        self.telegram = telegram_notifier
        self._running = False
        
        logger.info(
            f"SignalWatcher initialized (check_interval={check_interval}s)"
        )
    
    def run(self):
        """
        Main watcher loop - runs continuously until stopped.
        
        This is a blocking call. Run in separate thread/process if needed.
        """
        self._running = True
        logger.info("🔍 SignalWatcher started")
        
        while self._running:
            try:
                self.check_cycle()
            except KeyboardInterrupt:
                logger.info("SignalWatcher stopped by user")
                break
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error in watcher cycle: {error_msg}")
                if "API_BLOCKED" in error_msg and self.telegram:
                    self.telegram.send_critical_alert(f"TwelveData API Blocked or Invalid: {error_msg}")
            
            time.sleep(self.check_interval)
        
        logger.info("SignalWatcher stopped")
    
    def stop(self):
        """Stop the watcher loop gracefully"""
        self._running = False
    
    def check_cycle(self):
        """
        Single check cycle:
        1. Fetch active signals
        2. Get latest market data
        3. Check each signal for state transitions
        """
        # 1. Fetch active signals
        signals = self.fetch_active_signals()
        
        if not signals:
            logger.debug("No active signals to watch")
            return
        
        logger.info(f"Watching {len(signals)} active signals")
        
        # 2. Get latest market data
        candle = self.fetch_latest_candle()
        
        if not candle:
            logger.warning("Failed to fetch market data, skipping cycle")
            return
        
        logger.debug(
            f"Latest candle: {candle['timestamp']} "
            f"H:{candle['high']} L:{candle['low']} C:{candle['close']}"
        )
        
        # 3. Check each signal
        for signal in signals:
            try:
                self.check_signal(signal, candle)
            except Exception as e:
                logger.error(
                    f"Error checking signal {signal.get('id')}: {e}",
                    exc_info=True
                )
    
    def fetch_active_signals(self) -> List[dict]:
        """
        Fetch signals in WAITING_FOR_ENTRY or ENTRY_HIT states.
        
        Returns:
            List of signal dictionaries
        """
        try:
            response = self.db.table("fx_signals").select("*").in_(
                "state",
                ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
            ).execute()
            
            return response.data or []
        
        except Exception as e:
            logger.error(f"Error fetching active signals: {e}")
            return []
    
    def fetch_latest_candle(self) -> Optional[dict]:
        """
        Fetch latest M15 candle from TwelveData.
        
        Returns:
            Candle dict with timestamp, open, high, low, close
            or None if fetch fails
        """
        try:
            # Use direct API call instead of pandas
            # TwelveData REST API endpoint
            import requests
            import os
            
            api_key = os.getenv("TWELVE_DATA_API_KEY")
            url = "https://api.twelvedata.com/time_series"
            
            params = {
                "symbol": "EUR/USD",
                "interval": "15min",
                "outputsize": 1,
                "apikey": api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "error":
                logger.warning(f"TwelveData API error: {data.get('message')}")
                return None
            
            if "values" not in data or not data["values"]:
                logger.warning("No candle data returned from TwelveData")
                return None
            
            # Get latest candle (first in values array)
            latest = data["values"][0]
            
            return {
                "timestamp": latest.get("datetime"),
                "open": float(latest.get("open", 0)),
                "high": float(latest.get("high", 0)),
                "low": float(latest.get("low", 0)),
                "close": float(latest.get("close", 0))
            }
        
        except Exception as e:
            logger.error(f"Error fetching candle: {e}")
            return None
    
    def check_signal(self, signal: dict, candle: dict):
        """
        Check single signal for state transitions.
        
        Routes to appropriate checker based on current state.
        """
        signal_id = signal.get("id")
        current_state = signal.get("state")
        
        logger.debug(f"Checking signal {signal_id} (state={current_state})")
        
        if current_state == "WAITING_FOR_ENTRY":
            self.check_waiting_signal(signal, candle)
        
        elif current_state == "ENTRY_HIT":
            self.check_entry_hit_signal(signal, candle)
    
    def check_waiting_signal(self, signal: dict, candle: dict):
        """
        Check WAITING_FOR_ENTRY signal for:
        1. Entry touch (priority)
        2. Expiry
        """
        signal_id = signal.get("id")
        
        # Priority 1: Check entry touch
        if self.is_entry_touched(signal, candle):
            logger.info(f"✅ Entry touched for signal {signal_id}")
            self.transition_to_entry_hit(signal, candle)
            return
        
        # Priority 2: Check expiry
        current_time = datetime.now(timezone.utc)
        expiry_str = signal.get("expiry_at")
        
        if expiry_str:
            # Parse expiry time (handle both Z and +00:00 formats)
            expiry_at = datetime.fromisoformat(
                expiry_str.replace("Z", "+00:00")
            )
            
            if current_time >= expiry_at:
                logger.info(f"⚠️ Signal {signal_id} expired without entry")
                self.transition_to_cancelled(signal)
    
    def check_entry_hit_signal(self, signal: dict, candle: dict):
        """
        Check ENTRY_HIT signal for:
        1. TP touch (priority)
        2. SL touch
        """
        signal_id = signal.get("id")
        
        # Priority 1: Check TP
        if self.is_tp_touched(signal, candle):
            logger.info(f"🎯 TP hit for signal {signal_id}")
            self.transition_to_tp_hit(signal, candle)
            return
        
        # Priority 2: Check SL
        if self.is_sl_touched(signal, candle):
            logger.info(f"🛑 SL hit for signal {signal_id}")
            self.transition_to_sl_hit(signal, candle)
    
    # ========================================
    # TOUCH DETECTION METHODS
    # ========================================
    
    def is_entry_touched(self, signal: dict, candle: dict) -> bool:
        """
        Check if entry price was touched in this candle.
        
        BUY: Entry touched when price drops to entry level (low <= entry)
        SELL: Entry touched when price rises to entry level (high >= entry)
        """
        entry = signal.get("entry_price")
        direction = signal.get("direction")
        
        if not entry or not direction:
            return False
        
        if direction == "BUY":
            return candle["low"] <= entry
        else:  # SELL
            return candle["high"] >= entry
    
    def is_tp_touched(self, signal: dict, candle: dict) -> bool:
        """
        Check if take profit was touched.
        
        BUY: TP touched when price rises to TP (high >= tp)
        SELL: TP touched when price drops to TP (low <= tp)
        """
        tp = signal.get("tp")
        direction = signal.get("direction")
        
        if not tp or not direction:
            return False
        
        if direction == "BUY":
            return candle["high"] >= tp
        else:  # SELL
            return candle["low"] <= tp
    
    def is_sl_touched(self, signal: dict, candle: dict) -> bool:
        """
        Check if stop loss was touched.
        
        BUY: SL touched when price drops to SL (low <= sl)
        SELL: SL touched when price rises to SL (high >= sl)
        """
        sl = signal.get("sl")
        direction = signal.get("direction")
        
        if not sl or not direction:
            return False
        
        if direction == "BUY":
            return candle["low"] <= sl
        else:  # SELL
            return candle["high"] >= sl
    
    # ========================================
    # STATE TRANSITION METHODS
    # ========================================
    
    def transition_to_entry_hit(self, signal: dict, candle: dict):
        """
        Transition: WAITING_FOR_ENTRY → ENTRY_HIT
        
        Updates:
        - state = ENTRY_HIT
        - entry_hit_at = candle timestamp
        """
        signal_id = signal.get("id")
        
        try:
            self.db.table("fx_signals").update({
                "state": "ENTRY_HIT",
                "entry_hit_at": candle["timestamp"]
            }).eq("id", signal_id).execute()
            
            logger.success(f"Signal {signal_id} → ENTRY_HIT")
            
            # Send Telegram notification
            if self.telegram:
                self.telegram.send_entry_hit(signal)
        
        except Exception as e:
            logger.error(f"Failed to transition signal {signal_id} to ENTRY_HIT: {e}")
    
    def transition_to_tp_hit(self, signal: dict, candle: dict):
        """
        Transition: ENTRY_HIT → TP_HIT
        
        Updates:
        - state = TP_HIT
        - result = PROFIT
        - closed_at = candle timestamp
        """
        signal_id = signal.get("id")
        
        try:
            self.db.table("fx_signals").update({
                "state": "TP_HIT",
                "result": "PROFIT",
                "closed_at": candle["timestamp"]
            }).eq("id", signal_id).execute()
            
            logger.success(f"Signal {signal_id} → TP_HIT (PROFIT)")
            
            # Send Telegram notification
            if self.telegram:
                self.telegram.send_tp_hit(signal)
        
        except Exception as e:
            logger.error(f"Failed to transition signal {signal_id} to TP_HIT: {e}")
    
    def transition_to_sl_hit(self, signal: dict, candle: dict):
        """
        Transition: ENTRY_HIT → SL_HIT
        
        Updates:
        - state = SL_HIT
        - result = LOSS
        - closed_at = candle timestamp
        """
        signal_id = signal.get("id")
        
        try:
            self.db.table("fx_signals").update({
                "state": "SL_HIT",
                "result": "LOSS",
                "closed_at": candle["timestamp"]
            }).eq("id", signal_id).execute()
            
            logger.success(f"Signal {signal_id} → SL_HIT (LOSS)")
            
            # Send Telegram notification
            if self.telegram:
                self.telegram.send_sl_hit(signal)
        
        except Exception as e:
            logger.error(f"Failed to transition signal {signal_id} to SL_HIT: {e}")
    
    def transition_to_cancelled(self, signal: dict):
        """
        Transition: WAITING_FOR_ENTRY → CANCELLED
        
        Updates:
        - state = CANCELLED
        - result = CANCELLED
        - closed_at = current time
        """
        signal_id = signal.get("id")
        
        try:
            self.db.table("fx_signals").update({
                "state": "CANCELLED",
                "result": "CANCELLED",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", signal_id).execute()
            
            logger.success(f"Signal {signal_id} → CANCELLED (expired)")
            
            # Send Telegram notification
            if self.telegram:
                self.telegram.send_cancelled(signal)
        
        except Exception as e:
            logger.error(f"Failed to transition signal {signal_id} to CANCELLED: {e}")
