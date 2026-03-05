"""
Retroactive Signal Auditor v1.0
================================
Fetches actual historical price data from Binance for past signals,
checks if TP or SL was actually hit, and updates the database.

This corrects signals that were incorrectly marked as EXPIRED/TIMEOUT
because the Watcher was offline.

Usage:
    python backend/retroactive_audit.py [--dry-run] [--limit N]
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import requests
import time
from datetime import datetime, timezone, timedelta
from loguru import logger

from quantix_core.database.connection import db
from quantix_core.config.settings import settings

# --- CONFIG ---
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
SYMBOL = "EURUSDT"
HIT_TOLERANCE = 0.00005  # 0.5 pips (same as Watcher)
DRY_RUN = "--dry-run" in sys.argv

# --- HELPERS ---

def fetch_binance_candles(start_time: datetime, end_time: datetime, interval: str = "1m"):
    """Fetch historical 1m candles from Binance between start and end time."""
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    all_candles = []
    current_start = start_ms
    
    while current_start < end_ms:
        params = {
            "symbol": SYMBOL,
            "interval": interval,
            "startTime": current_start,
            "endTime": end_ms,
            "limit": 1000  # Binance max
        }
        
        try:
            resp = requests.get(BINANCE_KLINES_URL, params=params, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Binance returned {resp.status_code}")
                break
            
            data = resp.json()
            if not data:
                break
            
            for candle in data:
                ts = datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc)
                all_candles.append({
                    "timestamp": ts,
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4])
                })
            
            # Move forward
            current_start = data[-1][0] + 60000  # Next minute
            time.sleep(0.1)  # Rate limit
            
        except Exception as e:
            logger.error(f"Binance fetch failed: {e}")
            break
    
    return all_candles


def check_signal_outcome(signal: dict, candles: list) -> dict:
    """
    Walk through historical candles to determine if TP or SL was hit.
    Returns: {"result": "PROFIT"/"LOSS"/"TIMEOUT", "hit_time": datetime, "hit_price": float}
    """
    direction = signal.get("direction", "BUY")
    entry = signal.get("entry_price", 0)
    tp = signal.get("tp", 0)
    sl = signal.get("sl", 0)
    state = signal.get("state", "")
    
    # Determine the start of monitoring
    start_str = signal.get("entry_hit_at") or signal.get("generated_at")
    if not start_str:
        return {"result": "UNKNOWN", "reason": "No start time"}
    
    start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
    max_duration = settings.MAX_TRADE_DURATION_MINUTES  # 180m
    
    # For WAITING_FOR_ENTRY signals, first check if entry was ever hit
    was_entry_hit = (state == "ENTRY_HIT") or (signal.get("entry_hit_at") is not None)
    entry_hit_time = None
    
    for candle in candles:
        ct = candle["timestamp"]
        h = candle["high"]
        l = candle["low"]
        
        if not was_entry_hit:
            # Check if entry was hit first
            gen_at = datetime.fromisoformat(signal.get("generated_at", "").replace("Z", "+00:00"))
            pending_limit = gen_at + timedelta(minutes=settings.MAX_PENDING_DURATION_MINUTES)
            
            if ct > pending_limit:
                return {"result": "EXPIRED", "reason": f"Entry window expired ({settings.MAX_PENDING_DURATION_MINUTES}m)", "hit_time": pending_limit}
            
            # Check SL invalidation
            if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                return {"result": "SL_INVALIDATED", "reason": "SL hit before entry", "hit_time": ct}
            if direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                return {"result": "SL_INVALIDATED", "reason": "SL hit before entry", "hit_time": ct}
            
            # Check entry touch
            if direction == "BUY" and l <= (entry + HIT_TOLERANCE):
                was_entry_hit = True
                entry_hit_time = ct
                start_time = ct  # Reset timer for trade duration
                continue
            elif direction == "SELL" and h >= (entry - HIT_TOLERANCE):
                was_entry_hit = True
                entry_hit_time = ct
                start_time = ct
                continue
        else:
            # Entry already hit — check TP/SL
            trade_age = (ct - start_time).total_seconds() / 60
            
            # TP Check (PRIORITY: check TP first)
            if direction == "BUY" and h >= (tp - HIT_TOLERANCE):
                return {
                    "result": "PROFIT",
                    "reason": f"TP hit at {h:.5f}",
                    "hit_time": ct,
                    "hit_price": h,
                    "entry_hit_time": entry_hit_time
                }
            if direction == "SELL" and l <= (tp + HIT_TOLERANCE):
                return {
                    "result": "PROFIT",
                    "reason": f"TP hit at {l:.5f}",
                    "hit_time": ct,
                    "hit_price": l,
                    "entry_hit_time": entry_hit_time
                }
            
            # SL Check
            if direction == "BUY" and l <= (sl + HIT_TOLERANCE):
                return {
                    "result": "LOSS",
                    "reason": f"SL hit at {l:.5f}",
                    "hit_time": ct,
                    "hit_price": l,
                    "entry_hit_time": entry_hit_time
                }
            if direction == "SELL" and h >= (sl - HIT_TOLERANCE):
                return {
                    "result": "LOSS",
                    "reason": f"SL hit at {h:.5f}",
                    "hit_time": ct,
                    "hit_price": h,
                    "entry_hit_time": entry_hit_time
                }
            
            # Timeout
            if trade_age >= max_duration:
                return {
                    "result": "TIMEOUT",
                    "reason": f"Trade reached {max_duration}m limit",
                    "hit_time": ct,
                    "hit_price": candle["close"],
                    "entry_hit_time": entry_hit_time
                }
    
    return {"result": "TIMEOUT", "reason": "Candle data ended before resolution"}


def main():
    limit_arg = 50
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit_arg = int(sys.argv[i + 1])
    
    print("=" * 80)
    print(f"RETROACTIVE SIGNAL AUDITOR {'(DRY RUN)' if DRY_RUN else '(LIVE UPDATE)'}")
    print(f"Checking last {limit_arg} closed signals against Binance historical data")
    print("=" * 80)
    
    # Fetch closed signals (EXPIRED, TIMEOUT, CANCELLED)
    res = db.client.table(settings.TABLE_SIGNALS).select("*").in_(
        "status", ["EXPIRED", "CLOSED_TIMEOUT", "SL_INVALIDATED"]
    ).order("generated_at", desc=True).limit(limit_arg).execute()
    
    signals = res.data or []
    print(f"\nFound {len(signals)} signals to audit.\n")
    
    stats = {"PROFIT": 0, "LOSS": 0, "TIMEOUT": 0, "EXPIRED": 0, "SL_INVALIDATED": 0, "UNCHANGED": 0, "ERROR": 0}
    
    for i, sig in enumerate(signals):
        sig_id = sig.get("id", "???")[:8]
        direction = sig.get("direction", "?")
        entry = sig.get("entry_price", 0)
        tp = sig.get("tp", 0)
        sl = sig.get("sl", 0)
        status = sig.get("status", "?")
        gen_at_str = sig.get("generated_at", "")
        
        print(f"\n--- [{i+1}/{len(signals)}] Signal {sig_id} | {direction} @ {entry:.5f} | TP: {tp:.5f} SL: {sl:.5f} | Was: {status} ---")
        
        if not gen_at_str:
            print(f"  [SKIP] No generated_at timestamp")
            stats["ERROR"] += 1
            continue
        
        gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
        
        # Calculate time window: from signal generation to max possible close
        # Entry window (35m) + Trade duration (180m) + buffer (10m) = ~225m
        end_time = gen_at + timedelta(minutes=settings.MAX_PENDING_DURATION_MINUTES + settings.MAX_TRADE_DURATION_MINUTES + 10)
        
        print(f"  Fetching Binance data: {gen_at.strftime('%Y-%m-%d %H:%M')} → {end_time.strftime('%H:%M')} UTC...")
        candles = fetch_binance_candles(gen_at, end_time)
        
        if not candles:
            print(f"  [ERROR] No candle data from Binance")
            stats["ERROR"] += 1
            continue
        
        print(f"  Got {len(candles)} candles. Scanning...")
        
        # Run retroactive check
        outcome = check_signal_outcome(sig, candles)
        result = outcome.get("result", "UNKNOWN")
        reason = outcome.get("reason", "")
        hit_time = outcome.get("hit_time")
        
        # Determine if this changes the original status
        if result == "PROFIT":
            new_state = "TP_HIT"
            new_status = "CLOSED_TP"
            new_result = "PROFIT"
            pips = abs(tp - entry) * 10000
            print(f"  *** PROFIT FOUND! *** {reason} | +{pips:.1f} pips")
            stats["PROFIT"] += 1
        elif result == "LOSS":
            new_state = "SL_HIT"
            new_status = "CLOSED_SL"
            new_result = "LOSS"
            pips = abs(entry - sl) * 10000
            print(f"  *** LOSS FOUND! *** {reason} | -{pips:.1f} pips")
            stats["LOSS"] += 1
        elif result == "EXPIRED":
            print(f"  [CONFIRMED] {reason}")
            stats["EXPIRED"] += 1
            continue  # No change needed
        elif result == "SL_INVALIDATED":
            print(f"  [CONFIRMED] {reason}")
            stats["SL_INVALIDATED"] += 1
            continue
        else:
            print(f"  [CONFIRMED] Timeout: {reason}")
            stats["TIMEOUT"] += 1
            continue  # No change needed
        
        # UPDATE DATABASE
        if not DRY_RUN:
            try:
                update_data = {
                    "state": new_state,
                    "status": new_status,
                    "result": new_result,
                    "closed_at": hit_time.isoformat() if hit_time else datetime.now(timezone.utc).isoformat()
                }
                # Also update entry_hit_at if we discovered entry was hit
                if outcome.get("entry_hit_time"):
                    update_data["entry_hit_at"] = outcome["entry_hit_time"].isoformat()
                
                db.client.table(settings.TABLE_SIGNALS).update(
                    update_data
                ).eq("id", sig.get("id")).execute()
                
                print(f"  [DB UPDATED] {sig_id} → {new_state} ({new_result})")
            except Exception as e:
                print(f"  [DB ERROR] {e}")
                stats["ERROR"] += 1
        else:
            print(f"  [DRY RUN] Would update {sig_id} → {new_state} ({new_result})")
    
    # SUMMARY
    print("\n" + "=" * 80)
    print("RETROACTIVE AUDIT SUMMARY")
    print("=" * 80)
    print(f"  Signals Audited : {len(signals)}")
    print(f"  PROFIT (TP Hit) : {stats['PROFIT']} {'*NEW*' if stats['PROFIT'] > 0 else ''}")
    print(f"  LOSS (SL Hit)   : {stats['LOSS']} {'*NEW*' if stats['LOSS'] > 0 else ''}")
    print(f"  Timeout         : {stats['TIMEOUT']} (confirmed)")
    print(f"  Expired         : {stats['EXPIRED']} (confirmed)")
    print(f"  SL Invalidated  : {stats['SL_INVALIDATED']} (confirmed)")
    print(f"  Errors          : {stats['ERROR']}")
    
    if stats['PROFIT'] + stats['LOSS'] > 0:
        total_resolved = stats['PROFIT'] + stats['LOSS']
        win_rate = stats['PROFIT'] / total_resolved * 100
        print(f"\n  ** Actual Win Rate: {win_rate:.1f}% ({stats['PROFIT']}W / {stats['LOSS']}L) **")
    
    print("=" * 80)


if __name__ == "__main__":
    main()
