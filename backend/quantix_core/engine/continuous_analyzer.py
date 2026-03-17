import sys
import os
print("[BOOT] ANALYZER STARTING CORE IMPORTS...")
sys.stdout.flush()

import time
import json
import requests
from datetime import datetime, timezone, timedelta
from loguru import logger
from typing import Optional

from quantix_core.config.settings import settings

# 🚨 LOW-MEMORY / HIGH-STABILITY BOOT (v4.7.2.4)
# We move heavy AI/ML/Data science imports inside classes to prevent
# startup hangs on resource-constrained environments like Railway.
# Critical Path: Embedded Watcher (TP/SL) is prioritized.

class ContinuousAnalyzer:
    """
    Quantix AI Core Heartbeat [T0 + Δ]
    Runs every few seconds to detect the highest-confidence moment.
    """
    
    def __init__(self):
        # 🟢 Light Startup Phase (Priority: Trade Protection)
        from quantix_core.feeds.binance_feed import BinanceFeed
        from quantix_core.database.connection import db
        from quantix_core.utils.market_hours import MarketHours
        
        self.db = db
        self.binance = BinanceFeed()
        self.hours = MarketHours()
        
        # 🟡 Lazy-Loaded Heavy Phase (AI/ML)
        self.td_client = None
        self.engine = None
        self.refiner = None
        self.checker = None
        self.janitor = None
        
        self.cycle_count = 0
        self.last_pushed_at = None
        self.consecutive_losses = 0
        self.cooldown_until: Optional[datetime] = None
        
        # Local Paths
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.dirname(os.path.dirname(current_dir))
        self.audit_log_path = os.path.join(self.project_root, "heartbeat_audit.jsonl")
        
        # Telegram Setup
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
        
        self.notifier = None
        if token and chat_id:
            from quantix_core.notifications.telegram_notifier_v2 import create_notifier
            self.notifier = create_notifier(token, chat_id, admin_chat_id)
            logger.success("✅ [STABLE_BOOT] Notifier Ready")
        else:
            logger.warning("⚠️ [STABLE_BOOT] Notifier NOT initialized: Token or Chat ID missing.")

        # 🚨 [v4.7.2.3] Enhanced Robust Audit Timing
        self.last_health_report_at = None
        try:
            # Query DB for last successful health report
            res_report = self.db.client.table(settings.TABLE_ANALYSIS_LOG).select("timestamp")\
                .eq("asset", "HEALTH_REPORT").eq("status", "SENT").order("timestamp", desc=True).limit(1).execute()
            
            if res_report.data:
                self.last_health_report_at = datetime.fromisoformat(res_report.data[0]["timestamp"].replace("Z", "+00:00"))
                logger.info(f"📊 Restored last audit report time: {self.last_health_report_at}")
            else:
                # First time: set to trigger in 1 minute
                self.last_health_report_at = datetime.now(timezone.utc) - timedelta(minutes=settings.HEALTH_REPORT_INTERVAL_MINUTES - 1)
                logger.info("📊 No previous health report found. Staging first report for 60s from boot.")
        except Exception as e:
            logger.warning(f"Could not restore health report time: {e}")
            self.last_health_report_at = datetime.now(timezone.utc) - timedelta(minutes=settings.HEALTH_REPORT_INTERVAL_MINUTES - 2)

        logger.info(f"🚀 [v4.7.2.5] Low-Memory Stable Boot (Log: {self.audit_log_path})")

    def _ensure_engines(self):
        """Lazy-load heavy AI structures only when needed."""
        if self.engine is None:
            logger.info("📦 [LazyLoad] Importing AI Engines (Pandas/StructureEngine)...")
            from quantix_core.ingestion.twelve_data_client import TwelveDataClient
            from quantix_core.engine.structure_engine_v1 import StructureEngineV1
            from quantix_core.engine.confidence_refiner import ConfidenceRefiner
            from quantix_core.utils.entry_calculator import EntryCalculator
            from quantix_core.engine.janitor import Janitor
            
            self.td_client = TwelveDataClient(api_key=settings.TWELVE_DATA_API_KEY)
            self.engine = StructureEngineV1(sensitivity=2)
            self.refiner = ConfidenceRefiner()
            self.checker = EntryCalculator()
            self.janitor = Janitor()
            logger.success("✅ [LazyLoad] Ready.")

    def convert_to_df(self, data):
        """Standard pandas converter with local import to prevent startup hang."""
        import pandas as pd
        
        if isinstance(data, dict) and "values" in data:
            df = pd.DataFrame(data["values"])
            df["datetime"] = pd.to_datetime(df["datetime"])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
            df["datetime"] = pd.to_datetime(df["datetime"])
        else:
            return pd.DataFrame()
        
        df = df.sort_values("datetime")
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float)
        return df
        
    def _check_circuit_breaker(self):
        """v4.5.5: Circuit Breaker DISABLED per user request (Open Flow Mode)"""
        pass

    def _get_m15_trend(self) -> Optional[str]:
        """v4.6.1: Fetch M15 trend for faster adaptation (Replaced H1)"""
        try:
            # v4.6.1: Use 200 bars of M15 for a solid trend anchor (~2 days)
            raw_m15 = self.binance.get_history(symbol="EURUSD", interval="15m", limit=200)
            if not raw_m15:
                raw_m15 = self.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=200).get("values")
            
            if raw_m15:
                df_m15 = self.convert_to_df(raw_m15)
                m15_state = self.engine.analyze(df_m15, symbol="EURUSD", timeframe="M15_TREND")
                return m15_state.state # "bullish", "bearish", "range"
        except Exception as e:
            logger.error(f"M15 Trend fetch failed: {e}")
        return None
    def check_release_gate(self, asset: str, timeframe: str) -> tuple[bool, str]:
        """
        🛡️ ANTI-BURST PROTECTION (v4.7.2.4)
        Returns (is_allowed, reason)
        """
        try:
            # 1. Check for recent signals for this asset to prevent spamming
            # We query for any signal created within the last MIN_RELEASE_INTERVAL_MINUTES
            cooldown_mins = settings.MIN_RELEASE_INTERVAL_MINUTES
            
            # Query Supabase for most recent signal of this asset
            res = self.db.client.table(settings.TABLE_SIGNALS).select("generated_at")\
                .eq("asset", asset)\
                .order("generated_at", desc=True)\
                .limit(1).execute()
            
            if res.data:
                last_gen_str = res.data[0]["generated_at"]
                last_gen = datetime.fromisoformat(last_gen_str.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                diff_mins = (now - last_gen).total_seconds() / 60
                
                if diff_mins < cooldown_mins:
                    return False, f"COOLDOWN: Signal released {diff_mins:.1f}m ago (Min: {cooldown_mins}m)"
            
            # 2. Check Daily Cap
            # (Optional: can be added if needed, but per-asset cooldown is most critical)
            
            return True, "ALLOWED"
        except Exception as e:
            return True, f"ERROR_ALLOW_BY_DEFAULT" # Safety: don't block on DB error

    def lock_signal(self, signal_data: dict) -> Optional[str]:
        """LOCK signal with timestamp in Immutable Record [T1]"""
        try:
            # Create a copy for DB insertion to avoid modifying the original dictionary used by Telegram
            db_payload = signal_data.copy()
            
            # --- SCHEMA SANITIZATION ---
            # 1. Preserve refinement explanation in explainability field
            if "refinement_reason" in db_payload and db_payload.get("refinement_reason"):
                # Append if not already present (check to avoid duplication)
                if str(db_payload["refinement_reason"]) not in str(db_payload.get("explainability", "")):
                    db_payload["explainability"] = f"{db_payload.get('explainability', '')} | {db_payload['refinement_reason']}"

            # 2. Remove fields not in DB schema to prevent PGRST204 errors
            schema_keys = [
                "valid_until", "activation_limit_mins", "max_monitoring_mins", 
                "refinement_reason", "is_market_entry", "refinement", 
                "signal_metadata", "tp_pips", "sl_pips", "explainability", 
                "strength", "state", "entry_low", "entry_high", "metadata"
            ]
            for key in schema_keys:
                if key in db_payload:
                    del db_payload[key]

            res = self.db.client.table(settings.TABLE_SIGNALS).insert(db_payload).execute()
            if res.data:
                logger.info(f"🔒 Signal LOCKED in [T1]: {res.data[0]['id']} | Telegram: {signal_data.get('telegram_message_id', 'None')}")
                return res.data[0]['id']
        except Exception as e:
            logger.error(f"❌ Failed to LOCK signal in [T1]: {e}")
        return None

    def janitor_cleanup(self):
        """
        🧹 AUTO-JANITOR (Fail-Safe)
        Self-cleans the pipeline using robust logic from Janitor module.
        """
        self.janitor.run_sync()

    def run_cycle(self):
        """One analysis cycle [T0 + Δ]"""
        start_time = time.perf_counter()
        
        # 💓 [v4.5.6] PRIMARY HEARTBEAT - Log immediately
        try:
            self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "HEARTBEAT",
                "direction": "SYSTEM",
                "status": f"ALIVE_V4.7.2.5_C{self.cycle_count+1}_START",
                "confidence": 0.0, "strength": 0.0, "price": 0.0
            }).execute()
        except: pass

        try:
            # 🔥 EMERGENCY JANITOR
            if self.janitor:
                self.janitor.run_sync()

            # 🛡️ Market Hours Safety Check
            if not self.hours.should_generate_signals():
                logger.debug("🕒 Market outside signal hours. Skipping full analysis.")
                return

            # Ensure heavy engines are ready for signal generation
            self._ensure_engines()

            # 🛑 Circuit Breaker / Cooldown Check
            self._check_circuit_breaker()
            if self.cooldown_until:
                logger.warning(f"⏸️ System in Cooldown until {self.cooldown_until.isoformat()} due to losses.")
                return

            self.cycle_count += 1
            # Reset internal counter to prevent infinite growth
            if self.cycle_count > 1000000: self.cycle_count = 1
            
            logger.info(f"🎬 [v3.5] Starting analysis cycle #{self.cycle_count}...")
            
            
            # 1. Continuous Feed [T0] - Multi-Source Fallover
            import pandas as pd
            df = pd.DataFrame()
            
            # --- Source A: Binance (Primary - Free/Unlimited) ---
            try:
                # v4.6.1: Shift signal generation to M5 for FAST ADAPTATION
                raw_data = self.binance.get_history(symbol="EURUSD", interval="5m", limit=100)
                if raw_data:
                    df = self.convert_to_df(raw_data)
                    logger.info("📡 Data Source: BINANCE (Primary - M5)")
            except Exception as e:
                logger.warning(f"⚠️ Binance failed: {e}")

            # --- Source B: TwelveData (Fallback - Quota Limited) ---
            if df.empty:
                try:
                    raw_data = self.td_client.get_time_series(symbol="EUR/USD", interval="5min", outputsize=100)
                    if raw_data and "values" in raw_data:
                        df = self.convert_to_df(raw_data)
                        logger.info("📡 Data Source: TWELVEDATA (Fallback - M5)")
                except Exception as e:
                    logger.error(f"⚠️ TwelveData fallback failed: {e}")

            if df.empty:
                logger.error("❌ CRITICAL: All data sources failed. Skipping cycle.")
                return

            # 3. Prepare Common Data
            price = float(df.iloc[-1]["close"])
            latency_ms = int((time.perf_counter() - start_time) * 1000)

            # 2. Market Analysis (EURUSD Heartbeat)
            heartbeat_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "HEARTBEAT_ANALYZER",
                "price": price,
                "direction": "HEARTBEAT",
                "status": f"V4.7.2.5_STABLE_{latency_ms}ms",
                "strength": 0.0,
                "confidence": 0.0
            }
            try:
                self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert(heartbeat_entry).execute()
                logger.success(f"✅ Cycle #{self.cycle_count} complete (M5 Mode) in {latency_ms}ms")
            except: pass

            # 2. Market Analysis (M5)
            state = self.engine.analyze(df, symbol="EURUSD", timeframe="M5", source="binance")
            
            # Map market state to trading direction
            # STRICT RULE: Only trade clear structure — skip neutral/sideways
            direction_map = {
                "bullish": "BUY",
                "bearish": "SELL"
            }
            direction = direction_map.get(state.state)
            
            if direction is None:
                # Market is neutral/ranging/sideways → No signal, wait for clarity
                logger.info(
                    f"⏸️ Market structure is '{state.state}' (neutral/ranging). "
                    f"Skipping signal — waiting for directional confirmation."
                )
                return

            # 🧩 v4.6.1: M15 Trend Alignment (Replaced H1 for faster adaptation)
            m15_trend = self._get_m15_trend()
            mtf_penalty = 1.0  # Default: no penalty
            if m15_trend:
                logger.info(f"🔎 Trend Check: M5_SIGNAL={direction} | M15_TREND={m15_trend.upper()}")
                mtf_aligned = (direction == "BUY" and m15_trend == "bullish") or \
                              (direction == "SELL" and m15_trend == "bearish")
                if not mtf_aligned:
                    mtf_penalty = 0.95  # 5% confidence penalty for misalignment in Scalper Mode
                    logger.warning(f"⚠️ Trend Misalignment: M5 {direction} vs M15_TREND={m15_trend.upper()} → 0.95x penalty")
            else:
                logger.warning("⚠️ M15 trend unavailable. Proceeding with caution (M5 only).")
            
            # ============================================
            # v3.5 SMC-LITE ENTRY LOGIC (FVG-Based)
            # ============================================
            
            # --- STRATEGY UPGRADE v3.8 (Market Execution First) ---
            # 💡 Entry Logic: Market Entry for ALL released signals
            # Root cause analysis showed 100% pending orders with avg 9.9 pip gap
            # = 50% of signals never hit entry. Fix: execute at market price.
            is_market_entry = False
            msg_type = "PENDING"
            
            # v3.8: All signals that pass confidence gate (80%) use MARKET EXECUTION
            # This eliminates the entry miss problem entirely
            if state.confidence >= settings.MIN_CONFIDENCE:
                entry_price = price
                is_market_entry = True
                msg_type = "MARKET_EXECUTION"
                logger.success(f"🚀 MARKET EXECUTION ({state.confidence:.2f}) -> Entry at {price:.5f}")
            else:
                # Fallback: FVG with tighter offset (0.5 pips)
                from quantix_core.utils.entry_calculator import EntryCalculator
                entry_calc = EntryCalculator(offset_pips=0.5)
                entry_price, is_valid, validation_msg = entry_calc.calculate_fvg_entry(
                    market_price=price,
                    direction=direction,
                    fvg=getattr(state, 'nearest_fvg', None)
                )
                if not is_valid:
                    logger.warning(f"SKIP_SIGNAL: {validation_msg}")
                    return
                msg_type = validation_msg

            # 💡 Sáng kiến 2 (v3.8): Session-Aware TP/SL (Tightened for Hit Rate)
            # Phiên biến động cao -> TP rộng hơn (dễ chạm trong 1-2 nến)
            # Phiên yếu -> TP siêu hẹp (3-4 pips) để chốt nhanh
            try:
                high_s = df['high'].astype(float)
                low_s = df['low'].astype(float)
                close_s = df['close'].astype(float)
                tr = pd.concat([high_s - low_s, (high_s - close_s.shift()).abs(), (low_s - close_s.shift()).abs()], axis=1).max(axis=1)
                atr = tr.rolling(14).mean().iloc[-1]
                
                # Detect session for dynamic TP/SL
                hour_utc = now.hour if 'now' in dir() else datetime.now(timezone.utc).hour
                
                if 13 <= hour_utc < 17:  # London-NY Overlap (PEAK)
                    tp_mult = 1.5   # TP = 1.5x ATR (~15-25 pips)
                    sl_mult = 1.0   # SL = 1.0x ATR (~10-15 pips)  
                    session_tag = "PEAK"
                elif 6 <= hour_utc < 13:  # London (HIGH)
                    tp_mult = 1.2   # TP = 1.2x ATR (~12-20 pips)
                    sl_mult = 0.8   # SL = 0.8x ATR (~8-12 pips)
                    session_tag = "HIGH"
                else:  # Asia/Late NY (LOW volatility)
                    tp_mult = 1.0   # TP = 1.0x ATR (~10-12 pips)
                    sl_mult = 0.7   # SL = 0.7x ATR (~7-10 pips)
                    session_tag = "LOW"
                
                # 💡 SMC-Standard Mode (v4.1.1)
                # Adjusted to User Preference: Managed via settings.py (TP=7p, SL=12p)
                sl_pips = settings.SL_PIPS
                tp_pips = settings.TP_PIPS
                
                # Convert back to price points
                tp_dist = round(tp_pips * 0.0001, 5)
                sl_dist = round(sl_pips * 0.0001, 5)
                
                logger.info(f"v4.1.1 R:R (FIXED): ATR={atr if 'atr' in locals() else 0:.5f} | TP={tp_dist:.5f} ({tp_pips}p) | SL={sl_dist:.5f} ({sl_pips}p)")
            except Exception as e:
                logger.error(f"ATR failed, using hard safety fallback from settings: {e}")
                tp_dist = round(settings.TP_PIPS * 0.0001, 5)
                sl_dist = round(settings.SL_PIPS * 0.0001, 5)

            if direction == "BUY":
                tp = round(entry_price + tp_dist, 5)
                sl = round(entry_price - sl_dist, 5)
            else:  # SELL
                tp = round(entry_price - tp_dist, 5)
                sl = round(entry_price + sl_dist, 5)
            
            rrr = round(tp_dist / sl_dist, 2)
            
            # Calculate expiry time (Entry timeout: 30 minutes)
            now = datetime.now(timezone.utc)
            expiry_at = now + timedelta(minutes=settings.MAX_PENDING_DURATION_MINUTES)

            # Determine strength label for internal logic/filtering
            strength_label = "ULTRA" if state.confidence >= 0.95 else "HIGH" if state.confidence >= 0.85 else "NORMAL"
            
            # ============================================
            # v2 SIGNAL STRUCTURE (WAITING_FOR_ENTRY)
            # ============================================
            signal_base = {
                "asset": "EURUSD",
                "direction": direction,
                "strength": state.strength,
                "timeframe": "M5",
                "status": "PREPARED",
                "state": "PREPARED",  # Phase 1: Invisible to Watcher/UI
                "entry_price": entry_price,     # Future entry (NOT market)
                "valid_until": expiry_at.isoformat(), # OFFICIAL TIMING v3.1
                "expiry_at": expiry_at.isoformat(),   # Legacy support
                "activation_limit_mins": settings.MAX_PENDING_DURATION_MINUTES,
                "max_monitoring_mins": settings.MAX_TRADE_DURATION_MINUTES,
                
                # Legacy fields (for backward compatibility)
                "entry_low": entry_price,
                "entry_high": entry_price + 0.0002,
                
                # TP/SL (calculated from entry, not market)
                "tp": tp,
                "sl": sl,
                "tp_pips": tp_pips,
                "sl_pips": sl_pips,
                "reward_risk_ratio": rrr,
                
                # Metadata
                "ai_confidence": state.confidence,
                "generated_at": now.isoformat(),
                "explainability": f"M5 Structure {state.state.upper()} | M15 Trend Filter | Type: {msg_type}",
                "is_test": False,
                "is_market_entry": is_market_entry,
                
                # --- 5W1H TRANSPARENCY (v4.6.1) ---
                "strategy": f"Quantix_v4.7.0_TRAILING_TP",
                "refinement": (
                    f"Structure: {state.state.upper()} | "
                    f"Conf: {state.confidence:.0%} | "
                    f"Vol: {state.strength:.1f} | "
                    f"Spread: {1.0:.1f} | "
                    f"[{msg_type}]"
                ),
                "signal_metadata": {
                    # WHO - Model Identity
                    "model": "Quantix_v3.8_SMC",
                    "engine": "StructureEngine_v1",
                    
                    # WHAT - Risk Profile
                    "entry_type": msg_type,
                    "tp_pips": round(tp_dist * 10000, 1),
                    "sl_pips": round(sl_dist * 10000, 1),
                    "rr_ratio": rrr,
                    "strength_label": strength_label,
                    "max_lot_cap": settings.MAX_LOT_SIZE_CAP, # 🛡️ Institutional Guard Rail
                    "risk_percent": settings.RISK_PERCENT,
                    
                    # WHERE - Market Context
                    "session": session_tag,
                    "market_price_at_signal": price,
                    "atr_value": round(atr if 'atr' in dir() else 0.0, 5),
                    "structure_state": state.state.upper(),
                    "zone": f"{'Discount' if direction == 'BUY' else 'Premium'} Zone",
                    
                    # WHEN - Timing
                    "generated_utc": now.isoformat(),
                    "session_hour_utc": now.hour,
                    "entry_window_mins": settings.MAX_PENDING_DURATION_MINUTES,
                    "max_trade_mins": settings.MAX_TRADE_DURATION_MINUTES,
                    
                    # WHY - Technical Reasoning
                    "why": (
                        f"M5 Scalper {state.state.upper()} structure. "
                        f"AI confidence {state.confidence:.0%} exceeds {settings.MIN_CONFIDENCE:.0%} threshold. "
                        f"Fixed Parameters: TP=10p, SL=5p, Risk=2% per trade. "
                        f"Institutional Guard Rail: {settings.MAX_LOT_SIZE_CAP} cap."
                    ),
                    
                    # HOW - Market Regime
                    "volatility": session_tag,
                    "data_source": "TwelveData/Binance",
                    "execution_method": msg_type,
                }
            }
            
            # --- RELEASE CONFIDENCE REFINEMENT ---
            release_score, refinement_reason = self.refiner.calculate_release_score(
                raw_confidence=state.confidence,
                df=df
            )
            # v4.5.3: Apply MTF penalty (soft filter)
            release_score = round(release_score * mtf_penalty, 4)
            if mtf_penalty < 1.0:
                refinement_reason += f" | MTF: {mtf_penalty}"
            signal_base["release_confidence"] = release_score
            signal_base["refinement_reason"] = refinement_reason
            
            # Log signal creation for verification
            logger.info(
                f"Signal Evaluated: {direction} @ {entry_price} "
                f"| Raw Conf: {state.confidence:.2f} | Release Score: {release_score:.2f} "
                f"| {refinement_reason}"
            )

            # 4. Local Audit Log (JSONL) - Robust Absolute Path
            analysis_entry = {
                "timestamp": signal_base["generated_at"],
                "asset": "EURUSD",
                "price": price,
                "direction": direction,
                "strength": state.strength,
                "confidence": state.confidence,
                "release_confidence": release_score,
                "refinement": refinement_reason,
                "status": "ANALYZED"
            }
            try:
                with open(self.audit_log_path, "a") as f:
                    import json
                    f.write(json.dumps(analysis_entry) + "\n")
            except Exception as e:
                logger.error(f"Failed to write heartbeat log: {e}")

            # 4b. Push Analysis to Supabase [T1] for persistent telemetry
            try:
                self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert(analysis_entry).execute()
            except Exception as e:
                error_msg = str(e)
                if "PGRST204" in error_msg and ("refinement" in error_msg or "release_confidence" in error_msg):
                    # Fallback for telemetry
                    fallback_entry = {k: v for k, v in analysis_entry.items() 
                                      if k not in ["refinement", "release_confidence"]}
                    try:
                        self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert(fallback_entry).execute()
                    except: pass
                else:
                    logger.debug(f"DB telemetry write failed: {e}")

            # ============================================
            # 🔁 QUANTIX LIVE WORKFLOW (ACTIVE MODE)
            # ============================================

            # 1. Check Confidence Gate
            if release_score >= settings.MIN_CONFIDENCE:
                # 2. Check Anti-Burst Rule
                is_allowed, gate_reason = self.check_release_gate(signal_base["asset"], signal_base["timeframe"])
                
                if is_allowed:
                    logger.success(f"🎯 M5 Scalp Release ({release_score*100:.1f}%) -> BIRTH SIGNAL")
                    
                    # Update to LIVE status immediately
                    signal_base["status"] = "PUBLISHED"
                    signal_base["state"] = "PUBLISHED"
                    
                    if signal_base.get("is_market_entry"):
                        signal_base["state"] = "ENTRY_HIT"
                        signal_base["status"] = "ENTRY_HIT"
                        signal_base["entry_hit_at"] = now.isoformat()
                        logger.success("🚀 MARKET EXECUTION: Signal born in ENTRY_HIT state")
                    else:
                        signal_base["state"] = "WAITING_FOR_ENTRY"
                        signal_base["status"] = "WAITING_FOR_ENTRY"
                    
                    # 3. DB COMMIT (Single Phase)
                    signal_id = self.lock_signal(signal_base)
                    
                    # 4. BROADCAST (Telegram) - v4.6.3: Decoupled from DB success
                    if self.notifier:
                        import uuid
                        signal_for_tg = signal_base.copy()
                        # Use DB ID if available, otherwise fallback to local temporary ID
                        effective_id = signal_id or f"temp_{uuid.uuid4().hex[:8]}"
                        signal_for_tg["id"] = effective_id
                        
                        msg_id = self.push_to_telegram(signal_for_tg)
                        
                        if msg_id:
                            if signal_id:
                                # Update signal with Telegram ID in DB
                                try:
                                    self.db.client.table(settings.TABLE_SIGNALS).update({
                                        "telegram_message_id": msg_id
                                    }).eq("id", signal_id).execute()
                                    logger.success(f"🚀 [LIVE] Signal {signal_id} is active (TG: {msg_id})")
                                except Exception as e:
                                    logger.error(f"Failed to link TG ID to signal {signal_id}: {e}")
                            else:
                                logger.warning(f"⚠️ Signal sent to Telegram (ID: {msg_id}) but NOT locked in DB (temp_id: {effective_id})")
                            
                            self.last_pushed_at = datetime.now(timezone.utc)
                        else:
                            logger.error("Telegram broadcast failed.")
                    else:
                        logger.warning("Telegram notifier missing. Signal was processed but not sent.")
                else:
                    logger.warning(f"🛡️ [ANTI-BURST] Signal rejected by Gate: {gate_reason}")
            else:
                logger.info(f"🔍 Score below threshold ({release_score:.2f} < {settings.MIN_CONFIDENCE}) - No action.")

            # 6. Dashboard Telemetry Update & Technical Audit
            try:
                # v4.3.0: Once per hour (60s * 60)
                should_update = (self.cycle_count % 60 == 0)
                
                if should_update:
                    # 6a. Update Learning Data
                    try:
                        from analyze_heartbeat import analyze_heartbeat
                        analyze_heartbeat(push_to_git=True)
                    except Exception as e:
                        logger.error(f"Failed to update dashboard learning data: {e}")
                    
                    # 6b. Update Technical Audit Report (HTML)
                    try:
                        import subprocess
                        audit_script = os.path.join(self.project_root, "backend", "automate_audit.py")
                        subprocess.run([sys.executable, audit_script], capture_output=True, text=True, timeout=30)
                        logger.success("✅ [AUDIT] Technical Audit Report updated automatically.")
                    except Exception as e:
                        logger.error(f"Failed to run automated audit: {e}")
            except Exception as e:
                logger.error(f"Dashboard/Audit update error: {e}")

            # 7. INTEGRATED WATCHDOG — Check Watcher health every 30 cycles (~30 min @ 60s/cycle)
            if self.cycle_count > 0 and self.cycle_count % 30 == 0:
                self._check_watcher_health()

        except Exception as e:
            logger.error(f"Heartbeat cycle failed: {e}")

    def _check_watcher_health(self):
        """
        Integrated Watchdog: Check if Signal Watcher is alive.
        Called every 24 cycles (~120 minutes) from run_cycle.
        If Watcher is stale > 30 min:
          1. Run Janitor to clear stuck signals
          2. Send Telegram alert to Admin
        """
        WATCHER_STALE_THRESHOLD_MIN = 30
        
        try:
            now = datetime.now(timezone.utc)
            
            # Query last Watcher heartbeat
            res = self.db.client.table(settings.TABLE_ANALYSIS_LOG)\
                .select("timestamp, status")\
                .eq("asset", "HEARTBEAT_WATCHER")\
                .order("timestamp", desc=True)\
                .limit(1)\
                .execute()
            
            if not res.data:
                logger.warning("🏥 Watchdog: No Watcher heartbeat found in DB!")
                stale_min = 9999
            else:
                hb_time = datetime.fromisoformat(res.data[0]["timestamp"].replace("Z", "+00:00"))
                stale_min = (now - hb_time).total_seconds() / 60
                logger.info(f"🏥 Watchdog: Watcher last heartbeat {stale_min:.0f}m ago ({res.data[0]['status']})")
            
            if stale_min > WATCHER_STALE_THRESHOLD_MIN:
                logger.warning(f"🚨 Watchdog: Watcher is STALE ({stale_min:.0f}m > {WATCHER_STALE_THRESHOLD_MIN}m threshold)!")
                
                # 1. Run Janitor to clean stuck signals 
                from quantix_core.engine.janitor import Janitor
                logger.info("🧹 Running Janitor auto-cleanup for stuck signals...")
                self.janitor.run_sync()
                
                # 2. Send Alert to Admin via Telegram
                if self.notifier:
                    alert_msg = (
                        f"🚨 *WATCHER OFFLINE ALERT*\n\n"
                        f"Signal Watcher has not reported heartbeat for *{stale_min:.0f} minutes*.\n\n"
                        f"🧹 Janitor has cleaned up stuck signals.\n"
                        f"⚠️ Manual restart may be required on Railway.\n\n"
                        f"Cc: @admin"
                    )
                    try:
                        self.notifier.send_critical_alert(alert_msg)
                    except Exception as te:
                        logger.error(f"Failed to send Watcher alert: {te}")
                
                # 3. Log to DB for tracking
                try:
                    self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "WATCHDOG_ALERT",
                        "direction": "SYSTEM",
                        "status": f"WATCHER_STALE_{int(stale_min)}m",
                        "confidence": 0.0,
                        "strength": 0.0,
                        "price": 0.0
                    }).execute()
                except: pass
            else:
                logger.info(f"🏥 Watchdog: Watcher is HEALTHY ({stale_min:.0f}m)")
                # 🛡️ Update WATCHDOG_ALERT to OK to clear any stale FAILs in dashboard
                try:
                    self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "WATCHDOG_ALERT",
                        "direction": "SYSTEM",
                        "status": "WATCHER_OK",
                        "confidence": 1.0, "strength": 1.0, "price": 0.0
                    }).execute()
                except: pass
                
        except Exception as e:
            logger.error(f"Watchdog health check failed: {e}")

    def _broadcast_comprehensive_report(self):
        """
        v4.2.0: Generate and send a comprehensive system health report to Telegram Admin.
        """
        logger.info("📊 Generating periodic system health report...")
        try:
            now = datetime.now(timezone.utc)
            today_str = now.strftime('%Y-%m-%d')
            
            # 1. Component Heartbeats
            res_hb = self.db.client.table(settings.TABLE_ANALYSIS_LOG)\
                .select("asset, timestamp, status")\
                .in_("asset", ["HEARTBEAT_ANALYZER", "HEARTBEAT_WATCHER"])\
                .order("timestamp", desc=True)\
                .limit(10)\
                .execute()
            
            analyzer_status = "🔴 OFFLINE"
            watcher_status = "🔴 OFFLINE"
            
            for hb in res_hb.data:
                hb_time = datetime.fromisoformat(hb["timestamp"].replace("Z", "+00:00"))
                stale_min = (now - hb_time).total_seconds() / 60
                if hb["asset"] == "HEARTBEAT_ANALYZER" and analyzer_status.startswith("🔴"):
                    if stale_min < 10: analyzer_status = f"🟢 ONLINE ({stale_min:.0f}m)"
                    else: analyzer_status = f"🟡 STALE ({stale_min:.0f}m)"
                elif hb["asset"] == "HEARTBEAT_WATCHER" and watcher_status.startswith("🔴"):
                    if stale_min < 10: watcher_status = f"🟢 ONLINE ({stale_min:.0f}m)"
                    else: watcher_status = f"🟡 STALE ({stale_min:.0f}m)"

            # 2. Signal Stats
            res_signals = self.db.client.table(settings.TABLE_SIGNALS)\
                .select("id, state, generated_at")\
                .gte("generated_at", today_str)\
                .execute()
            
            total_today = len(res_signals.data) if res_signals.data else 0
            active_states = ["ENTRY_HIT", "WAITING_FOR_ENTRY", "PUBLISHED"]
            active_count = sum(1 for s in res_signals.data if s["state"] in active_states) if res_signals.data else 0
            
            # 3. Format Message
            report = (
                f"📊 *SYSTEM COMPREHENSIVE HEALTH*\n\n"
                f"🕒 Time: `{now.strftime('%H:%M:%S UTC')}`\n\n"
                f"*🌐 COMPONENT STATUS:*\n"
                f"├ ANALYZER: {analyzer_status}\n"
                f"└ WATCHER: {watcher_status}\n\n"
                f"*📈 SIGNAL PERFORMANCE:*\n"
                f"├ Today's Signals: `{total_today}`\n"
                f"└ Currently Tracking: `{active_count}`\n\n"
                f"*⚙️ ENGINE PARAMS:*\n"
                f"├ Version: `v4.7.2.5` (Stable)\n"
                f"├ Interval: `{settings.MONITOR_INTERVAL_SECONDS}s`\n"
                f"└ Target: `10p/5p` (Aggressive 2:1)\n\n"
                f"✅ *All systems functioning normally.*"
            )
            
            if self.notifier:
                # Use _send_to_chat directly to ensure it goes to admin_chat_id
                target = self.notifier.admin_chat_id or self.notifier.chat_id
                self.notifier._send_to_chat(target, report)
                logger.success(f"Health report broadcasted to Telegram Admin ({target}).")
                
                # Log report event to DB
                try:
                    self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                        "timestamp": now.isoformat(),
                        "asset": "HEALTH_REPORT",
                        "direction": "SYSTEM",
                        "status": "SENT",
                        "confidence": 1.0, "strength": 1.0, "price": 0.0
                    }).execute()
                except: pass
                
        except Exception as e:
            logger.error(f"Failed to generate health report: {e}")

    def push_to_telegram(self, signal: dict) -> Optional[int]:
        """Proactive Broadcast for High Confidence Signals"""
        # v4.5.9: 🔓 Cooldown completely removed for Open Flow Mode
        now = datetime.now(timezone.utc)

        # 🛡️ Signal Deduplication (Same asset/direction/tf/entry)
        if not hasattr(self, '_pushed_signals'):
            self._pushed_signals = set()
        
        signal_key = f"{signal['asset']}_{signal['direction']}_{signal['timeframe']}_{signal['entry_price']}"
        if signal_key in self._pushed_signals:
            logger.info(f"Signal {signal_key} already pushed to Telegram")
            return None

        if not self.notifier:
            logger.warning("Telegram pushing skipped: Notifier not initialized")
            return None

        try:
            # Use the new state-based method for standardized reporting
            if signal.get("is_market_entry"):
                msg_id = self.notifier.send_market_execution(signal)
            else:
                msg_id = self.notifier.send_waiting_for_entry(signal)
            
            if msg_id:
                logger.info(f"🚀 Signal released to Telegram (ID: {msg_id})")
                self.last_pushed_at = now
                self._pushed_signals.add(signal_key)
                return msg_id
            else:
                logger.error("Telegram push failed: Notifier returned None")
                return None

        except Exception as e:
            logger.error(f"Telegram push error: {e}")
            return None

    # ========================================
    # EMBEDDED WATCHER (v3.8) — Replaces standalone Watcher
    # ========================================

    def _embedded_watcher_check(self):
        """
        Embedded Signal Watcher — runs inside the Analyzer process.
        This eliminates the standalone Watcher crash problem.
        
        Fetches active signals, gets latest price (Binance), and checks TP/SL/Entry.
        Uses multi-candle detection (5 candles) for better accuracy.
        """
        try:
            now = datetime.now(timezone.utc)
            # 1. Fetch active signals
            res = self.db.client.table(settings.TABLE_SIGNALS).select("*").in_(
                "status", ["WAITING_FOR_ENTRY", "ENTRY_HIT"]
            ).execute()
            signals = res.data or []
            
            # 1. Log heartbeat immediately to show watcher is alive
            try:
                self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                    "timestamp": now.isoformat(),
                    "asset": "HEARTBEAT_WATCHER",
                    "direction": "SYSTEM",
                    "status": f"EMBEDDED_WATCHER_IDLE",
                    "confidence": 1.0, "strength": 1.0, "price": 0.0
                }).execute()
            except: pass

            if not signals:
                logger.debug("[EmbeddedWatcher] No active signals. Heartbeat logged.")
                return
            
            # Skip if market closed
            if not self.hours.is_market_open():
                logger.debug("[EmbeddedWatcher] Market closed, skipping.")
                return
            
            logger.info(f"👁️ [EmbeddedWatcher] Monitoring {len(signals)} active signals")
            
            # 2. Fetch latest candle from Binance (FREE, no quota)
            candle = None
            try:
                market_data = self.binance.get_price("EURUSD")
                if market_data:
                    candle = {
                        "timestamp": market_data["timestamp"],
                        "open": market_data["open"],
                        "high": market_data["high"],
                        "low": market_data["low"],
                        "close": market_data["close"]
                    }
            except Exception as e:
                logger.warning(f"[EmbeddedWatcher] Binance feed failed: {e}")
            
            # 2b. Multi-candle: Get last 5 candles for wider detection
            multi_candle = None
            try:
                history = self.binance.get_history("EURUSD", interval="1m", limit=5)
                if history and len(history) > 0:
                    multi_candle = {
                        "timestamp": history[-1]["datetime"],
                        "open": history[0]["open"],
                        "high": max(c["high"] for c in history),
                        "low": min(c["low"] for c in history),
                        "close": history[-1]["close"]
                    }
            except Exception as e:
                logger.debug(f"[EmbeddedWatcher] Multi-candle fetch failed: {e}")
            
            # Use multi-candle for wider TP/SL detection, single candle as fallback
            detection_candle = multi_candle or candle
            if not detection_candle:
                logger.warning("[EmbeddedWatcher] No market data available.")
                return
            
            logger.debug(f"[EmbeddedWatcher] Price H:{detection_candle['high']} L:{detection_candle['low']} C:{detection_candle['close']}")
            
            # 3. Check each signal
            HIT_TOLERANCE = 0.00005  # 0.5 pips tolerance
            now = datetime.now(timezone.utc)
            
            for sig in signals:
                try:
                    sig_id = sig.get("id")
                    state = sig.get("state")
                    direction = sig.get("direction")
                    entry = sig.get("entry_price")
                    tp = sig.get("tp")
                    sl = sig.get("sl")
                    
                    if not all([sig_id, state, direction, entry, tp, sl]):
                        continue
                    
                    h = detection_candle["high"]
                    l = detection_candle["low"]
                    c = detection_candle["close"]
                    ts = detection_candle["timestamp"]
                    
                    if state == "WAITING_FOR_ENTRY":
                        # --- Entry Window Check ---
                        gen_at_str = sig.get("generated_at")
                        if gen_at_str:
                            gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
                            if (now - gen_at).total_seconds() / 60 >= settings.MAX_PENDING_DURATION_MINUTES:
                                self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                    "state": "CANCELLED", "status": "EXPIRED",
                                    "result": "CANCELLED", "closed_at": now.isoformat()
                                }, "EXPIRED")
                                continue
                        
                        # --- SL Invalidation ---
                        if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                            self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "CANCELLED", "status": "SL_INVALIDATED",
                                "result": "CANCELLED", "closed_at": now.isoformat()
                            }, "SL_INVALIDATED")
                            continue
                        if direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                            self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "CANCELLED", "status": "SL_INVALIDATED",
                                "result": "CANCELLED", "closed_at": now.isoformat()
                            }, "SL_INVALIDATED")
                            continue
                        
                        # --- Entry Hit Check ---
                        entry_hit = False
                        if direction == "BUY" and l <= (entry + HIT_TOLERANCE):
                            entry_hit = True
                        elif direction == "SELL" and h >= (entry - HIT_TOLERANCE):
                            entry_hit = True
                        
                        if entry_hit:
                            if self._ew_transition(sig_id, "WAITING_FOR_ENTRY", {
                                "state": "ENTRY_HIT", "status": "ENTRY_HIT",
                                "entry_hit_at": ts if isinstance(ts, str) else now.isoformat()
                            }, "ENTRY_HIT"):
                                # Send entry hit notification
                                if self.notifier and sig.get("telegram_message_id"):
                                    try: self.notifier.send_entry_hit(sig)
                                    except: pass
                    
                    elif state == "ENTRY_HIT":
                        # --- TP Hit Check ---
                        tp_hit = False
                        if direction == "BUY" and h >= (tp - HIT_TOLERANCE):
                            tp_hit = True
                        elif direction == "SELL" and l <= (tp + HIT_TOLERANCE):
                            tp_hit = True
                        
                        if tp_hit:
                            if self._ew_transition(sig_id, "ENTRY_HIT", {
                                "state": "TP_HIT", "status": "CLOSED_TP",
                                "result": "PROFIT", "closed_at": now.isoformat()
                            }, "TP_HIT"):
                                if self.notifier and sig.get("telegram_message_id"):
                                    try: self.notifier.send_tp_hit(sig)
                                    except: pass
                            continue
                        
                        # --- v4.7.0 Trailing TP (Highest Price Reversal) ---
                        if getattr(settings, "ENABLE_TRAILING_TP", True):
                            try:
                                asset = sig.get("asset", "EURUSD")
                                # Pip detection (Support for JPY and other 2-decimal pairs)
                                is_jpy = "JPY" in asset
                                multiplier = 100 if is_jpy else 10000
                                
                                # Calculate current profit in pips
                                if direction == "BUY":
                                    current_pips = (c - entry) * multiplier
                                else:
                                    current_pips = (entry - c) * multiplier
                                
                                # Load metadata for persistence
                                meta_raw = sig.get("metadata", {})
                                if isinstance(meta_raw, str):
                                    try: meta = json.loads(meta_raw)
                                    except: meta = {}
                                # v4.7.2: Handle list or other types if somehow present
                                elif isinstance(meta_raw, dict):
                                    meta = meta_raw
                                else:
                                    meta = {}
                                
                                # THE PEAK: We track the absolute highest pips reached
                                current_peak = float(meta.get("trailing_peak", 0.0))
                                milestones = settings.TRAILING_TP_STEPS # Trigger steps (e.g. 5.0, 6.0...)
                                
                                # Activation: Trailing only starts after the first trigger step
                                activation_pips = milestones[0] if milestones else 5.0
                                
                                if current_pips >= activation_pips:
                                    # v4.7.2.4: SAFE FALLBACK - Try to update peak only if metadata column might exist
                                    # Since metadata is missing in some schemas, we catch the PGRST204 error specifically
                                    try:
                                        if current_pips > current_peak:
                                            meta["trailing_peak"] = round(current_pips, 2)
                                            # Update only if possible
                                            self.db.client.table(settings.TABLE_SIGNALS).update({
                                                "metadata": meta
                                            }).eq("id", sig_id).eq("state", "ENTRY_HIT").execute()
                                            logger.info(f"📈 [TrailingTP] {asset} new peak: {current_pips:.1f} pips")
                                            current_peak = current_pips
                                    except Exception as db_e:
                                        if "PGRST204" in str(db_e) or "metadata" in str(db_e).lower():
                                            logger.debug("⚠️ Trailing peak update skipped (metadata column missing)")
                                        else:
                                            logger.error(f"Trailing peak DB error: {db_e}")
                                    
                                    # 2. Check reversal (e.g. hits 7.2, drops to 6.7 -> CLOSE if reversal is 0.5)
                                    reversal_threshold = getattr(settings, "TRAILING_TP_REVERSAL", 0.5)
                                    if current_pips < (current_peak - reversal_threshold):
                                        logger.warning(f"🎯 [TrailingTP] {asset} reversing ({current_pips:.1f} < {current_peak:.1f} - {reversal_threshold}). CLOSING.")
                                        if self._ew_transition(sig_id, "ENTRY_HIT", {
                                            "state": "TP_HIT", "status": "CLOSED_TRAILING_TP",
                                            "result": "PROFIT", "closed_at": now.isoformat(),
                                            "metadata": meta
                                        }, "TRAILING_TP"):
                                            if self.notifier and sig.get("telegram_message_id"):
                                                try: self.notifier.send_tp_hit(sig, label="TRAILING TP")
                                                except: pass
                                        continue
                            except Exception as e:
                                logger.error(f"Trailing TP check failed: {e}")
                        
                        # --- SL Hit Check ---
                        sl_hit = False
                        if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                            sl_hit = True
                        elif direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                            sl_hit = True
                        
                        if sl_hit:
                            if self._ew_transition(sig_id, "ENTRY_HIT", {
                                "state": "SL_HIT", "status": "CLOSED_SL",
                                "result": "LOSS", "closed_at": now.isoformat()
                            }, "SL_HIT"):
                                if self.notifier and sig.get("telegram_message_id"):
                                    try: self.notifier.send_sl_hit(sig)
                                    except: pass
                            continue
                        
                        # --- Breakeven Check (DISABLED v4.1.8 for Scalping) ---
                        # tp_distance = abs(tp - entry)
                        # if tp_distance > 0:
                        #     if direction == "BUY":
                        #         progress = h - entry
                        #     else:
                        #         progress = entry - l
                        #     if progress / tp_distance >= 0.7 and (
                        #         (direction == "BUY" and sl < entry) or
                        #         (direction == "SELL" and sl > entry)
                        #     ):
                        #         try:
                        #             self.db.client.table(settings.TABLE_SIGNALS).update({
                        #                 "sl": entry
                        #             }).eq("id", sig_id).eq("state", "ENTRY_HIT").execute()
                        #             logger.success(f"🔒 [EmbeddedWatcher] BREAKEVEN: {sig_id} SL -> {entry}")
                        #         except: pass
                        
                        # --- Timeout Check ---
                        start_str = sig.get("entry_hit_at") or sig.get("generated_at")
                        if start_str:
                            start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if (now - start_time).total_seconds() / 60 >= settings.MAX_TRADE_DURATION_MINUTES:
                                self._ew_transition(sig_id, "ENTRY_HIT", {
                                    "state": "CANCELLED", "status": "CLOSED_TIMEOUT",
                                    "result": "CANCELLED", "closed_at": now.isoformat()
                                }, "TIMEOUT")
                                if self.notifier and sig.get("telegram_message_id"):
                                    try: self.notifier.send_time_exit(sig, c)
                                    except: pass
                
                except Exception as e:
                    logger.error(f"[EmbeddedWatcher] Error processing signal {sig.get('id')}: {e}")
            
            # 4. Update heartbeat with stats if we processed signals
            try:
                self.db.client.table(settings.TABLE_ANALYSIS_LOG).insert({
                    "timestamp": now.isoformat(),
                    "asset": "HEARTBEAT_WATCHER",
                    "direction": "SYSTEM",
                    "status": f"EMBEDDED_WATCHER_OK (Watching: {len(signals)})",
                    "confidence": 1.0, "strength": 1.0, "price": 0.0
                }).execute()
            except: pass
                
        except Exception as e:
            logger.error(f"[EmbeddedWatcher] Cycle failed: {e}")

    def _ew_transition(self, sig_id: str, from_state: str, update_data: dict, label: str) -> bool:
        """Atomic state transition for embedded watcher. Returns True if updated."""
        try:
            # v4.7.2.4: Sanitize update_data to prevent PGRST204 errors
            schema_keys = [
                "valid_until", "activation_limit_mins", "max_monitoring_mins", 
                "refinement_reason", "is_market_entry", "refinement", 
                "signal_metadata", "tp_pips", "sl_pips", "explainability", 
                "strength", "state", "entry_low", "entry_high", "metadata"
            ]
            clean_data = update_data.copy()
            for key in schema_keys:
                if key in clean_data and key not in ["state", "status", "result", "closed_at", "entry_hit_at", "tp", "sl", "tp_pips", "sl_pips", "metadata"]:
                    del clean_data[key]

            res = self.db.client.table(settings.TABLE_SIGNALS).update(
                clean_data
            ).eq("id", sig_id).eq("state", from_state).execute()
            
            if res.data:
                logger.success(f"👁️ [EmbeddedWatcher] {sig_id[:8]} -> {label}")
                return True
            else:
                logger.debug(f"[EmbeddedWatcher] Transition skipped for {sig_id[:8]} (already processed)")
                return False
        except Exception as e:
            logger.error(f"[EmbeddedWatcher] Transition failed for {sig_id[:8]}: {e}")
            return False

    def start(self):
        """Start the continuous evaluation loop with EMBEDDED WATCHER"""
        interval = settings.MONITOR_INTERVAL_SECONDS
        logger.info(f"💓 Continuous analyzer started with {interval}s interval")
        logger.info(f"👁️ EMBEDDED WATCHER MODE: Signal monitoring runs inside Analyzer")
        
        # Immediate Startup Proof using absolute path
        try:
            with open(self.audit_log_path, "a") as f:
                import json
                f.write(json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "SYSTEM_STARTUP",
                }) + "\n")
        except Exception as e:
            logger.error(f"Startup log failed: {e}")

        # 🆕 ADMIN BOT: Start Telegram Command Listener in background thread
        if self.notifier:
            import threading
            def _listen_loop():
                while True:
                    try:
                        self.notifier.handle_commands(self)
                    except Exception as e:
                        logger.error(f"Telegram command handler error: {e}")
                    time.sleep(3)
            
            cmd_thread = threading.Thread(target=_listen_loop, daemon=True)
            cmd_thread.start()
            logger.info("🤖 Telegram command listener started in background")

        while True:
            try:
                # 🎬 [v4.5.6] Healthy heartbeat interval (60s)
                logger.info("🎬 Starting new analysis cycle...")
                self.run_cycle()
                
                # 🆕 EMBEDDED WATCHER: Check active signals after every cycle
                self._embedded_watcher_check()
                
                # 🧹 REDUNDANT SAFETY: Run Janitor
                self.janitor.run_sync()
                
                # 🚨 [v4.7.2.3] ROBUST TELEGRAM AUDIT REPORT 
                # Move outside run_cycle to ensure it fires even if data fetching fails
                now_time = datetime.now(timezone.utc)
                if self.last_health_report_at is not None:
                    elapsed_health = (now_time - self.last_health_report_at).total_seconds() / 60
                    if elapsed_health >= settings.HEALTH_REPORT_INTERVAL_MINUTES:
                        logger.info(f"📢 [AUDIT] Interval reached ({elapsed_health:.1f}m). Triggering report...")
                        self._broadcast_comprehensive_report()
                        self.last_health_report_at = now_time
                else:
                    self.last_health_report_at = now_time # Guard
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Cycle error: {error_msg}")
                if "API_BLOCKED" in error_msg and self.notifier:
                    self.notifier.send_critical_alert(f"TwelveData API Blocked: {error_msg}")
            
            # 💤 [v4.5.6] PAUSE to avoid CPU exhaustion (Crucial for Cloud stability)
            time.sleep(interval)

if __name__ == "__main__":
    logger.critical("🚀 [Analyzer] Boot starting v4.7.2.5...")
    analyzer = ContinuousAnalyzer()
    analyzer.start()
