"""
Signal Watcher - Monitors active signals and executes state transitions

This module watches signals in WAITING_FOR_ENTRY and ENTRY_HIT states,
detects when price touches entry/TP/SL levels, and performs atomic state transitions.
"""

import time
import requests
import os
import threading
import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger
from supabase import Client
from quantix_core.utils.market_hours import MarketHours
from quantix_core.config.settings import settings


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
        supabase_client: Optional[Client] = None,
        td_client = None,
        check_interval: Optional[int] = None,
        telegram_notifier = None
    ):
        """Standardized Init for v3.2 embedding"""
        from quantix_core.database.connection import db
        from quantix_core.ingestion.twelve_data_client import TwelveDataClient
        
        self.db = supabase_client or db.client
        self.td_client = td_client or TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
        self.check_interval = check_interval or settings.WATCHER_CHECK_INTERVAL
        self._running = False
        
        # Auto-init telegram if not provided
        if telegram_notifier:
            self.telegram = telegram_notifier
        elif settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            from quantix_core.notifications.telegram_notifier_v2 import create_notifier
            self.telegram = create_notifier(
                settings.TELEGRAM_BOT_TOKEN, 
                settings.TELEGRAM_CHAT_ID,
                settings.TELEGRAM_ADMIN_CHAT_ID
            )
        else:
            self.telegram = None

        logger.info(
            f"SignalWatcher initialized (check_interval={self.check_interval}s)"
        )
    
    def run(self):
        """
        Main watcher loop - runs continuously until stopped.
        
        This is a blocking call. Run in separate thread/process if needed.
        """
        self._running = True
        logger.info("🔍 SignalWatcher started")
        
        # 🛡️ Disable Telegram on local to prevent duplicate notifications.
        # On Railway, RAILWAY_ENVIRONMENT is always set — use that as the truth.
        is_railway = os.getenv("RAILWAY_ENVIRONMENT") is not None
        if not is_railway and os.getenv("ENABLE_LOCAL_TELEGRAM", "false").lower() != "true":
            self.telegram = None
            logger.warning("🚫 LOCAL ENVIRONMENT: Telegram notifications DISABLED to prevent duplicates.")
        else:
            logger.info("✅ RAILWAY ENVIRONMENT: Telegram notifications ENABLED.")


        # 🤖 Start Telegram Command Listener in background thread (Only if telegram is enabled)
        if self.telegram:
            cmd_thread = threading.Thread(target=self._listen_for_commands, daemon=True)
            cmd_thread.start()
            logger.info("🤖 Telegram command listener started in background")

        # 🧹 Maintenance: Clear stuck signals from previous session or weekend
        try:
            from backend.expire_old_signals import expire_old
            asyncio.run(expire_old())
        except Exception as e:
            logger.warning(f"⚠️ Startup cleanup failed: {e}")

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

    def _cleanup_pending_on_close(self, signals: List[dict]):
        """Cancel all WAITING_FOR_ENTRY signals on Friday close."""
        for sig in signals:
            if sig.get("state") == "WAITING_FOR_ENTRY":
                logger.info(f"🚿 Market Closing: Cancelling pending signal {sig.get('id')}")
                self.transition_to_cancelled(sig)

    def _listen_for_commands(self):
        """Infinite loop for Telegram command polling (runs in thread)."""
        while self._running:
            try:
                if self.telegram:
                    self.telegram.handle_commands(watcher_instance=self)
            except Exception as e:
                logger.error(f"Error in command listener: {e}")
            time.sleep(3) # Poll every 3 seconds for responsive feel
    
    def check_cycle(self):
        """
        Single check cycle:
        1. Fetch active signals
        2. Get latest market data
        3. Check each signal for state transitions
        """
        # 1. Fetch active signals
        signals = self.fetch_active_signals()
        self.last_watched_count = len(signals)

        if not hasattr(self, 'cycle_count'): self.cycle_count = 0
        self.cycle_count += 1

        # 🛡️ Market Hours Check
        if not MarketHours.is_market_open():
            if signals:
                logger.warning(f"Market is CLOSED. Pausing watcher for {len(signals)} signals.")
            return
        
        if not signals:
            logger.debug("No active signals to watch")
            return
        
        logger.info(f"Watching {len(signals)} active signals")
        
        # 2. Get latest market data (Optional for timeouts, required for touches)
        candle = self.fetch_latest_candle()
        
        if candle:
            logger.debug(
                f"Latest candle: {candle['timestamp']} "
                f"H:{candle['high']} L:{candle['low']} C:{candle['close']}"
            )
        else:
            logger.warning("Failed to fetch market data - skipping touch detection but proceeding with timeout checks")
        
        # 3. Check each signal
        for signal in signals:
            try:
                # We always check for timeouts, price only needed for touch detection
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
        """Fetch latest candle with Multi-Source Fallover (Binance first to save TwelveData quota)"""
        # --- SOURCE A: BINANCE (FREE / NO KEY) ---
        try:
            # Binance is extremely fast and has no real quota for 1m requests
            resp = requests.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": "EURUSDT", "interval": "1m", "limit": 1},
                timeout=5
            )
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    c = data[0]
                    # Binance index: 1=Open, 2=High, 3=Low, 4=Close
                    logger.debug("✅ Market Data Source: BINANCE (Quota Protected)")
                    return {
                        "timestamp": datetime.fromtimestamp(c[0]/1000, tz=timezone.utc).isoformat(),
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4])
                    }
        except Exception as e:
            logger.warning(f"⚠️ Binance feed failed, falling back to TwelveData: {e}")

        # --- SOURCE B: TWELVEDATA (RESTRICTED QUOTA) ---
        try:
            data = self.td_client.get_time_series(
                symbol="EUR/USD",
                interval="1min",
                outputsize=2
            )
            
            if "values" not in data or not data["values"]:
                logger.warning("No candle data from TwelveData")
                return None
                
            latest = data["values"][0]
            logger.info("📡 Market Data Source: TWELVEDATA (Quota Used)")
            return {
                "timestamp": latest["datetime"],
                "open": float(latest["open"]),
                "high": float(latest["high"]),
                "low": float(latest["low"]),
                "close": float(latest["close"])
            }
        except Exception as e:
            logger.error(f"Error fetching TwelveData candle: {e}")
            return None
    
    def check_signal(self, signal: dict, candle: dict):
        """
        Check single signal for state transitions based on OFFICIAL TIMING MAP v3.1
        Strict Priority Order: 
        WAITING: Entry Window -> Entry Hit
        ACTIVE: TP/SL Hit -> 90m Duration Timeout
        """
        signal_id = signal.get("id")
        current_state = signal.get("state")
        now = datetime.now(timezone.utc)
        
        if current_state == "WAITING_FOR_ENTRY":
            # [1] ENTRY WINDOW CHECK
            # Use 'valid_until' if present, fallback to generated_at + 35m
            is_expired = False
            valid_until_str = signal.get("valid_until")
            if valid_until_str:
                valid_until = datetime.fromisoformat(valid_until_str.replace("Z", "+00:00"))
                if now > valid_until:
                    is_expired = True
            else:
                gen_at_str = signal.get("generated_at")
                if gen_at_str:
                    gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
                    if (now - gen_at).total_seconds() / 60 >= settings.MAX_PENDING_DURATION_MINUTES:
                        is_expired = True
            
            if is_expired:
                logger.info(f"⏱️ Signal {signal_id} CANCELLED (Entry Window Expired)")
                self.transition_to_cancelled(signal)
                return

            # [2] ENTRY HIT CHECK
            
            if candle and self.is_entry_touched(signal, candle):
                self.transition_to_entry_hit(signal, candle)
        
        elif current_state == "ENTRY_HIT":
            # [3] TP / SL CHECK
            if candle:
                if self.is_tp_touched(signal, candle):
                    self.transition_to_tp_hit(signal, candle)
                    return
                elif self.is_sl_touched(signal, candle):
                    self.transition_to_sl_hit(signal, candle)
                    return
            
            # [4] TRADE TIMEOUT (90m)
            # Checked after TP/SL to ensure we don't miss a winner on the same candle
            start_time_str = signal.get("entry_hit_at") or signal.get("generated_at")
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str.replace("Z", "+00:00"))
                if (now - start_time).total_seconds() / 60 >= settings.MAX_TRADE_DURATION_MINUTES:
                    logger.info(f"⏱️ Signal {signal_id} TIME_EXIT (Reached {settings.MAX_TRADE_DURATION_MINUTES}m limit)")
                    self.transition_to_time_exit(signal, candle)
                    return

    def check_waiting_signal(self, signal: dict, candle: dict):
        """Check if price touched entry level."""
        if self.is_entry_touched(signal, candle):
            self.transition_to_entry_hit(signal, candle)

    def check_entry_hit_signal(self, signal: dict, candle: dict):
        """Check if price touched TP or SL."""
        if self.is_tp_touched(signal, candle):
            self.transition_to_tp_hit(signal, candle)
        elif self.is_sl_touched(signal, candle):
            self.transition_to_sl_hit(signal, candle)
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
            is_touched = candle["low"] <= entry
            if is_touched:
                logger.info(f"🎯 BUY_ENTRY_TOUCH: {candle['low']} <= {entry}")
        else:  # SELL
            is_touched = candle["high"] >= entry
            if is_touched:
                logger.info(f"🎯 SELL_ENTRY_TOUCH: {candle['high']} >= {entry}")

        if is_touched:
            try:
                self.db.table("fx_analysis_log").insert({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "asset": signal.get("asset", "???"),
                    "direction": signal.get("direction", "???"),
                    "status": "ENTRY_TOUCH_DETECTED",
                    "price": candle.get("high" if direction == "SELL" else "low", 0),
                    "confidence": 0,
                    "strength": 0
                }).execute()
            except: pass
        return is_touched
    
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
        Atomic DB-First approach to prevent duplicate notifications.
        """
        signal_id = signal.get("id")
        
        try:
            # 1. ATOMIC DB UPDATE: Only proceed if state is still WAITING_FOR_ENTRY
            res = self.db.table("fx_signals").update({
                "state": "ENTRY_HIT",
                "status": "ENTRY_HIT",
                "entry_hit_at": candle["timestamp"]
            }).eq("id", signal_id).eq("state", "WAITING_FOR_ENTRY").execute()
            
            # If no rows were updated, it means another process already handled this
            if not res.data:
                logger.warning(f"⚠️ Signal {signal_id} transition skipped: Already processed or state mismatch.")
                return

            logger.success(f"✅ DB Update: Signal {signal_id} → ENTRY_HIT")

            # 2. SEND NOTIFICATION: Only after DB success
            tg_id = signal.get("telegram_message_id")
            if self.telegram and tg_id:
                self.telegram.send_entry_hit(signal)
            elif self.telegram and not tg_id:
                logger.info(f"ℹ️ Internal Signal {signal_id}: No Telegram ID, skipping notification.")
        
        except Exception as e:
            logger.error(f"❌ Failed to transition signal {signal_id} to ENTRY_HIT: {e}")

    def transition_to_tp_hit(self, signal: dict, candle: dict):
        """
        Transition: ENTRY_HIT → TP_HIT
        Atomic DB-First approach.
        """
        signal_id = signal.get("id")
        
        try:
            # 1. ATOMIC DB UPDATE
            res = self.db.table("fx_signals").update({
                "state": "TP_HIT",
                "status": "CLOSED_TP",
                "result": "PROFIT",
                "closed_at": candle["timestamp"]
            }).eq("id", signal_id).eq("state", "ENTRY_HIT").execute()
            
            if not res.data:
                return

            logger.success(f"🎯 DB Update: Signal {signal_id} → TP_HIT (PROFIT)")

            # 2. NOTIFICATION
            tg_id = signal.get("telegram_message_id")
            if self.telegram and tg_id:
                self.telegram.send_tp_hit(signal)
        
        except Exception as e:
            logger.error(f"❌ Failed to transition signal {signal_id} to TP_HIT: {e}")

    def transition_to_sl_hit(self, signal: dict, candle: dict):
        """
        Transition: ENTRY_HIT → SL_HIT
        Atomic DB-First approach.
        """
        signal_id = signal.get("id")
        
        try:
            # 1. ATOMIC DB UPDATE
            res = self.db.table("fx_signals").update({
                "state": "SL_HIT",
                "status": "CLOSED_SL",
                "result": "LOSS",
                "closed_at": candle["timestamp"]
            }).eq("id", signal_id).eq("state", "ENTRY_HIT").execute()
            
            if not res.data:
                return

            logger.success(f"🛑 DB Update: Signal {signal_id} → SL_HIT (LOSS)")

            # 2. NOTIFICATION
            tg_id = signal.get("telegram_message_id")
            if self.telegram and tg_id:
                self.telegram.send_sl_hit(signal)
        
        except Exception as e:
            logger.error(f"❌ Failed to transition signal {signal_id} to SL_HIT: {e}")

    def transition_to_cancelled(self, signal: dict):
        """
        Transition: WAITING_FOR_ENTRY → CANCELLED
        Atomic DB-First approach.
        """
        signal_id = signal.get("id")
        
        try:
            # 1. ATOMIC DB UPDATE
            res = self.db.table("fx_signals").update({
                "state": "CANCELLED",
                "status": "EXPIRED",
                "result": "CANCELLED",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", signal_id).eq("state", "WAITING_FOR_ENTRY").execute()
            
            if not res.data:
                return

            logger.success(f"⚪ DB Update: Signal {signal_id} → CANCELLED")

            # 2. NOTIFICATION
            tg_id = signal.get("telegram_message_id")
            if self.telegram and tg_id:
                self.telegram.send_cancelled(signal)
        
        except Exception as e:
            logger.error(f"❌ Failed to transition signal {signal_id} to CANCELLED: {e}")

    def transition_to_time_exit(self, signal: dict, candle: dict):
        """
        Transition: ENTRY_HIT → TIME_EXIT (CLOSED)
        Atomic DB-First approach.
        """
        signal_id = signal.get("id")
        current_price = candle.get("close")
        
        try:
            # 1. ATOMIC DB UPDATE
            res = self.db.table("fx_signals").update({
                "state": "TIME_EXIT",
                "status": "CLOSED_TIMEOUT",
                "result": "CANCELLED",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", signal_id).eq("state", "ENTRY_HIT").execute()
            
            if not res.data:
                return

            logger.success(f"⏱️ DB Update: Signal {signal_id} → TIME_EXIT")

            # 2. NOTIFICATION
            tg_id = signal.get("telegram_message_id")
            if self.telegram and tg_id:
                self.telegram.send_time_exit(signal, current_price)
        
        except Exception as e:
            logger.error(f"❌ Failed to transition signal {signal_id} to TIME_EXIT: {e}")

    def _is_already_closed(self, signal_id: str) -> bool:
        """Helper to check if a signal is already in a terminal state."""
        try:
            from quantix_core.config.settings import settings
            res = self.db.table(settings.TABLE_SIGNALS).select("status, state").eq("id", signal_id).execute()
            if res.data:
                sig = res.data[0]
                # Terminal states where we shouldn't send more notifications
                return sig.get("status") == "CLOSED" or sig.get("state") in ["TP_HIT", "SL_HIT", "CANCELLED", "TIME_EXIT"]
        except Exception:
            pass
        return False
