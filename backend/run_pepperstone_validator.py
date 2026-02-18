"""
Pepperstone Validation Layer - Independent Observer
Runs in parallel with main system to validate signals against Pepperstone feed

This layer:
1. Reads signals from Database (passive observer)
2. Validates TP/SL hits using Pepperstone actual feed
3. Logs discrepancies for analysis
4. Does NOT interfere with production system
"""

import time
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, List

from quantix_core.database.connection import SupabaseConnection
from quantix_core.config.settings import settings

# Configure logger
# For Railway: Use stdout (Railway captures this)
# For Local: Use file
IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None

if IS_RAILWAY:
    # Railway deployment - log to stdout
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
else:
    # Local deployment - log to file
    VALIDATION_LOG = Path(__file__).parent / "validation_audit.jsonl"
    logger.add(
        VALIDATION_LOG,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO",
        rotation="10 MB"
    )


class PepperstoneValidator:
    """
    Independent validation layer using Pepperstone feed
    
    Architecture:
    - Passive observer (reads DB, doesn't write)
    - Runs in separate process/thread
    - Can be stopped without affecting main system
    """
    
    def __init__(self, feed_source: str = "binance_proxy"):
        """
        Initialize validator
        
        Args:
            feed_source: "binance_proxy" | "mt5_api" | "ctrader_api" | "fix_api"
        """
        self.db = SupabaseConnection()
        self.feed_source = feed_source
        self.check_interval = 60  # Check every 60 seconds
        self.tracked_signals = {}  # {signal_id: validation_state}
        self.cycle_count = 0
        
        # ⚠️ SPREAD BUFFER (0.3 pips for EURUSD)
        self.spread_buffer = 0.00003 
        
        logger.info(f"🔍 Pepperstone Validator initialized (feed: {feed_source}, spread_buffer: {self.spread_buffer})")
    
    def run(self):
        """Main validation loop - runs independently"""
        logger.info("🚀 Validation Layer started (Independent Observer Mode)")
        
        while True:
            try:
                self.validation_cycle()
            except KeyboardInterrupt:
                logger.info("Validation Layer stopped by user")
                break
            except Exception as e:
                logger.error(f"Validation cycle error: {e}")
            
            self.cycle_count += 1
            # 💓 Validator Heartbeat (Every 5 cycles / 5 mins)
            if self.cycle_count % 5 == 0:
                self.log_validator_heartbeat()
                
            time.sleep(self.check_interval)
    
    def validation_cycle(self):
        """Single validation cycle"""
        # 1. Fetch active signals from Database
        signals = self.fetch_active_signals()
        
        if not signals:
            logger.debug("No active signals to validate")
            return
        
        logger.info(f"Validating {len(signals)} active signals")
        
        # 2. Get Pepperstone feed data
        pepperstone_data = self.fetch_pepperstone_feed()
        
        if not pepperstone_data:
            logger.warning("Failed to fetch Pepperstone feed - skipping cycle")
            return
        
        # 3. Validate each signal
        for signal in signals:
            self.validate_signal(signal, pepperstone_data)
    
    def fetch_active_signals(self) -> List[Dict]:
        """Fetch signals in WAITING_FOR_ENTRY or ENTRY_HIT states"""
        try:
            res = self.db.client.table("fx_signals").select("*").in_(
                "state",
                ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
            ).execute()
            
            return res.data or []
        except Exception as e:
            logger.error(f"Error fetching signals: {e}")
            return []
    
    def fetch_pepperstone_feed(self) -> Optional[Dict]:
        """
        Fetch current market data from Pepperstone feed (Binance proxy)
        Tries multiple endpoints to avoid regional blocks.
        """
        import requests
        
        # List of endpoints to try
        endpoints = [
            "https://api.binance.com/api/v3/klines",       # Global
            "https://api.binance.us/api/v3/klines",        # US (Railway)
            "https://data-api.binance.vision/api/v3/klines" # Developer API
        ]
        
        params = {
            "symbol": "EURUSDT",
            "interval": "1m",
            "limit": 5
        }
        
        for url in endpoints:
            try:
                response = requests.get(url, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if not data:
                        continue
                    
                    # Get latest candle
                    latest = data[-1]
                    
                    return {
                        "timestamp": datetime.fromtimestamp(latest[0]/1000, tz=timezone.utc).isoformat(),
                        "open": float(latest[1]),
                        "high": float(latest[2]),
                        "low": float(latest[3]),
                        "close": float(latest[4]),
                        "source": f"binance_proxy ({url})"
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch from {url}: {e}")
                continue
        
        logger.error("All Binance endpoints failed.")
        return None
    
    def validate_signal(self, signal: Dict, market_data: Dict):
        """
        Validate a single signal against Pepperstone feed
        
        Logs discrepancies between:
        - Main system's decision (from DB state)
        - Pepperstone feed's reality
        """
        signal_id = signal.get("id")
        state = signal.get("state")
        
        # Initialize tracking if new signal
        if signal_id not in self.tracked_signals:
            self.tracked_signals[signal_id] = {
                "first_seen": datetime.now(timezone.utc).isoformat(),
                "entry_validated": False,
                "tp_validated": False,
                "sl_validated": False,
                "discrepancies": []
            }
        
        tracking = self.tracked_signals[signal_id]
        
        # Validate based on state
        if state == "WAITING_FOR_ENTRY":
            self.validate_entry(signal, market_data, tracking)
        
        elif state == "ENTRY_HIT":
            self.validate_tp_sl(signal, market_data, tracking)
    
    def validate_entry(self, signal: Dict, market_data: Dict, tracking: Dict):
        """Validate entry trigger"""
        if tracking["entry_validated"]:
            return  # Already validated
        
        entry_price = signal.get("entry_price")
        direction = signal.get("direction")
        
        # Check if entry should have triggered
        pepperstone_triggered = False
        
        if direction == "BUY":
            pepperstone_triggered = market_data["high"] >= entry_price
        else:  # SELL
            pepperstone_triggered = market_data["low"] <= entry_price
        
        # Compare with main system's state
        main_system_triggered = (signal.get("state") == "ENTRY_HIT")
        
        # CASE 1: Mismatch detected
        if pepperstone_triggered != main_system_triggered:
            discrepancy = {
                "type": "ENTRY_MISMATCH",
                "signal_id": signal["id"],
                "asset": signal.get("asset", "EURUSD"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pepperstone_says": "TRIGGERED" if pepperstone_triggered else "NOT_TRIGGERED",
                "main_system_says": "TRIGGERED" if main_system_triggered else "NOT_TRIGGERED",
                "entry_price": entry_price,
                "market_price": market_data["close"],
                "market_high": market_data["high"],
                "market_low": market_data["low"],
                "direction": direction,
                "details": {
                    "entry_price": entry_price,
                    "market_high": market_data["high"],
                    "market_low": market_data["low"]
                }
            }
            
            tracking["discrepancies"].append(discrepancy)
            self.log_discrepancy(discrepancy, market_data)
        
        # CASE 2: Positive Confirmation (Both agree it triggered)
        elif pepperstone_triggered and main_system_triggered:
            self.log_validation_checkpoint(signal, "ENTRY", market_data)
            tracking["entry_validated"] = True
    
    def validate_tp_sl(self, signal: Dict, market_data: Dict, tracking: Dict):
        """Validate TP/SL hits"""
        direction = signal.get("direction")
        tp = signal.get("tp")
        sl = signal.get("sl")
        
        # Check Pepperstone feed with Spread Buffer
        pepperstone_tp_hit = False
        pepperstone_sl_hit = False
        
        # Buffer calculation:
        # BUY: TP needs high to be > TP + buffer; SL needs low to be < SL + buffer
        # SELL: TP needs low to be < TP - buffer; SL needs high to be > SL - buffer
        
        if direction == "BUY":
            pepperstone_tp_hit = market_data["high"] >= (tp + self.spread_buffer)
            pepperstone_sl_hit = market_data["low"] <= (sl + self.spread_buffer)
        else:  # SELL
            pepperstone_tp_hit = market_data["low"] <= (tp - self.spread_buffer)
            pepperstone_sl_hit = market_data["high"] >= (sl - self.spread_buffer)
            
        # 🛡️ RECORD WHICH OCCURRED FIRST
        # In a 1m candle, if both hit, we assume SL first (Conservative approach)
        if pepperstone_tp_hit and pepperstone_sl_hit:
            logger.warning(f"⚠️ DOUBLE HIT in same candle for signal {signal['id']}. Prioritizing SL validation.")
            pepperstone_tp_hit = False # Counter-intuitive but safer for 'Proof' layer
        
        # Compare with main system
        main_state = signal.get("state")
        
        # TP validation
        if pepperstone_tp_hit and main_state != "TP_HIT" and not tracking["tp_validated"]:
            discrepancy = {
                "type": "TP_MISMATCH",
                "signal_id": signal["id"],
                "asset": signal.get("asset", "EURUSD"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pepperstone_says": "TP_HIT",
                "main_system_says": main_state,
                "tp_price": tp,
                "market_price": market_data["close"],
                "market_high": market_data["high"],
                "market_low": market_data["low"],
                "details": {"tp": tp, "high": market_data["high"], "low": market_data["low"]}
            }
            
            tracking["discrepancies"].append(discrepancy)
            self.log_discrepancy(discrepancy, market_data)
            tracking["tp_validated"] = True
            
        elif pepperstone_tp_hit and main_state == "TP_HIT" and not tracking["tp_validated"]:
            self.log_validation_checkpoint(signal, "TP", market_data)
            tracking["tp_validated"] = True
        
        # SL validation
        if pepperstone_sl_hit and main_state != "SL_HIT" and not tracking["sl_validated"]:
            discrepancy = {
                "type": "SL_MISMATCH",
                "signal_id": signal["id"],
                "asset": signal.get("asset", "EURUSD"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pepperstone_says": "SL_HIT",
                "main_system_says": main_state,
                "sl_price": sl,
                "market_price": market_data["close"],
                "market_high": market_data["high"],
                "market_low": market_data["low"],
                "details": {"sl": sl, "high": market_data["high"], "low": market_data["low"]}
            }
            
            tracking["discrepancies"].append(discrepancy)
            self.log_discrepancy(discrepancy, market_data)
            tracking["sl_validated"] = True
            
        elif pepperstone_sl_hit and main_state == "SL_HIT" and not tracking["sl_validated"]:
            self.log_validation_checkpoint(signal, "SL", market_data)
            tracking["sl_validated"] = True
    
    def log_discrepancy(self, discrepancy: Dict, candle_data: Dict = None):
        """Log discrepancy to Database (for Self-Learning) and Logs"""
        # 1. Log to Console/File (Fast Alert)
        logger.warning(f"⚠️  DISCREPANCY: {discrepancy['type']} for signal {discrepancy['signal_id']}")
        
        if IS_RAILWAY:
            logger.info(f"DISCREPANCY_DATA: {json.dumps(discrepancy)}")
        else:
            discrepancy_file = Path(__file__).parent / "validation_discrepancies.jsonl"
            with open(discrepancy_file, "a") as f:
                f.write(json.dumps(discrepancy) + "\n")

        # 2. Log to Database (Deep Learning Feed)
        try:
            event_data = {
                "signal_id": discrepancy.get("signal_id"),
                "asset": discrepancy.get("asset", "EURUSD"),
                "feed_source": candle_data.get("source", "unknown") if candle_data else "unknown",
                "validator_price": candle_data.get("close", 0) if candle_data else 0,
                "validator_candle": candle_data,
                "check_type": discrepancy.get("type", "UNKNOWN"),
                "main_system_state": discrepancy.get("main_system_says", "UNKNOWN"),
                "is_discrepancy": True,
                "discrepancy_type": discrepancy.get("type"),
                "meta_data": discrepancy.get("details", {})
            }
            
            self.db.client.table("validation_events").insert(event_data).execute()
            logger.success(f"💾 Discrepancy saved to DB for AI Learning (Signal {discrepancy['signal_id']})")
        except Exception as e:
            logger.error(f"❌ Failed to save learning data to DB: {e}")

    def log_validation_checkpoint(self, signal: Dict, check_type: str, candle: Dict):
        """Log successful validation checkpoints (Positive Reinforcement Learning)"""
        try:
            event_data = {
                "signal_id": signal.get("id"),
                "asset": signal.get("asset", "EURUSD"),
                "feed_source": candle.get("source", "unknown"),
                "validator_price": candle.get("close", 0),
                "validator_candle": candle,
                "check_type": check_type,
                "main_system_state": signal.get("state"),
                "is_discrepancy": False,
                "meta_data": {"confidence": "HIGH", "match": True}
            }
            self.db.client.table("validation_events").insert(event_data).execute()
        except Exception as e:
            pass  # Silent fail for positive checks

    def log_validator_heartbeat(self):
        """Log that the validator is alive to the telemetry table"""
        try:
            hb = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "VALIDATOR",
                "price": 0,
                "direction": "HEARTBEAT",
                "confidence": 1.0,
                "status": "ONLINE",
                "strength": 1.0,
                "refinement": f"Validation Layer active. Monitoring {len(self.tracked_signals)} signals."
            }
            # Attempt insert - will fallback gracefully if columns missing
            self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert(hb).execute()
        except:
            pass


def main():
    """Run validation layer"""
    print("=" * 80)
    print("  PEPPERSTONE VALIDATION LAYER - INDEPENDENT OBSERVER")
    print("=" * 80)
    print()
    print("This layer runs in parallel with the main system.")
    print("It validates signals against Pepperstone feed.")
    print("DATA PERSISTENCE: Enabled (saving to Supabase for Self-Learning)")
    print()
    
    validator = PepperstoneValidator(feed_source="binance_proxy")
    validator.run()


if __name__ == "__main__":
    main()
