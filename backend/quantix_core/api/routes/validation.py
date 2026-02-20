"""
Validation API Routes — Phase 4 & 5 Production Monitoring
==========================================================
    GET /validation-logs          — Recent validation events
    GET /analysis-logs            — AI heartbeat logs
    GET /validation-status        — Phase 4 health monitor (HEALTHY/DEGRADED/CRITICAL)
    GET /validation-report        — Phase 3 spread analysis on-demand
    GET /auto-adjuster-report     — Phase 5.1 learned hour-matrix & ATR state
    GET /broker-comparison        — Phase 5.3 live spread across all brokers
    POST /broker-signal-check     — Phase 5.3 multi-broker entry hit check
"""


from fastapi import APIRouter, Query
from quantix_core.database.connection import db
from loguru import logger
from datetime import datetime, timezone, timedelta

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Existing endpoints (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/validation-logs")
async def get_validation_logs(limit: int = 50):
    """
    Fetch validation logs from Supabase.
    Used by Frontend to visualize Validator performance.
    """
    try:
        res = (
            db.client.table("validation_events")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return {"success": True, "data": res.data}
    except Exception as e:
        logger.error(f"Error fetching validation logs: {e}")
        return {"success": False, "error": str(e)}


@router.get("/analysis-logs")
async def get_analysis_logs(limit: int = 20):
    """
    Fetch AI Heartbeat (Analysis) logs from Supabase.
    Used by Frontend to show 'Thinking' activity.
    """
    try:
        res = (
            db.client.table("fx_analysis_log")
            .select("*")
            .order("timestamp", desc=True)
            .limit(limit)
            .execute()
        )
        return {"success": True, "data": res.data}
    except Exception as e:
        logger.error(f"Error fetching analysis logs: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 NEW: Production Monitoring Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/validation-status")
async def get_validation_status(days: int = Query(default=7, ge=1, le=90)):
    """
    Phase 4 Production Health Monitor.

    Returns a comprehensive status snapshot:
    - Validator uptime / last heartbeat
    - Discrepancy rate (last N days)
    - TP / SL / Entry mismatch breakdown
    - Current spread buffer recommendation
    - Feed source in use
    - Overall health rating: HEALTHY / DEGRADED / CRITICAL

    Used by:
    - Railway health dashboards
    - Frontend System Logs tab status badge
    - Automated monitoring alerts
    """
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # 1. Fetch validation events
        events = (
            db.client.table("validation_events")
            .select("is_discrepancy, check_type, feed_source, created_at, validator_candle")
            .gte("created_at", since)
            .neq("signal_id", "__health_check__")
            .order("created_at", desc=True)
            .execute()
        ).data or []

        total       = len(events)
        disc_events = [e for e in events if e.get("is_discrepancy")]
        disc_count  = len(disc_events)
        disc_rate   = round(disc_count / total * 100, 2) if total > 0 else 0.0

        # Mismatch breakdown
        tp_misses = sum(1 for e in disc_events if "TP" in (e.get("check_type") or ""))
        sl_misses = sum(1 for e in disc_events if "SL" in (e.get("check_type") or ""))
        en_misses = sum(1 for e in disc_events if "ENTRY" in (e.get("check_type") or ""))

        # 2. Last heartbeat (VALIDATOR asset in analysis log)
        hb_rows = (
            db.client.table("fx_analysis_log")
            .select("timestamp, status, strength")
            .eq("asset", "VALIDATOR")
            .order("timestamp", desc=True)
            .limit(1)
            .execute()
        ).data or []

        last_heartbeat   = hb_rows[0]["timestamp"] if hb_rows else None
        heartbeat_detail = hb_rows[0].get("status", "") if hb_rows else ""

        # Heartbeat age
        hb_age_minutes = None
        validator_online = False
        if last_heartbeat:
            hb_dt = datetime.fromisoformat(last_heartbeat.replace("Z", "+00:00"))
            hb_age_minutes = round(
                (datetime.now(timezone.utc) - hb_dt).total_seconds() / 60, 1
            )
            validator_online = hb_age_minutes < 15  # Online if heartbeat < 15m ago

        # 3. Feed source detection
        feed_sources = {e.get("feed_source") for e in events if e.get("feed_source")}
        active_feed  = sorted(feed_sources)[0] if feed_sources else "unknown"

        # 4. Spread stats from candle data
        spreads = []
        for e in events:
            candle = e.get("validator_candle") or {}
            bid, ask = candle.get("bid"), candle.get("ask")
            if bid and ask:
                spreads.append(round((ask - bid) * 10000, 2))  # pips

        spread_info = {}
        if spreads:
            import statistics
            spread_info = {
                "avg_pips": round(statistics.mean(spreads), 3),
                "max_pips": round(max(spreads), 3),
                "min_pips": round(min(spreads), 3),
            }

        # 5. Last event time
        last_event_at = events[0]["created_at"] if events else None

        # 6. Health rating
        if disc_rate < 5 and validator_online:
            health = "HEALTHY"
            health_emoji = "🟢"
        elif disc_rate < 10 or not validator_online:
            health = "DEGRADED"
            health_emoji = "🟡"
        else:
            health = "CRITICAL"
            health_emoji = "🔴"

        return {
            "success": True,
            "health":  health,
            "health_emoji": health_emoji,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days":  days,
            "validator": {
                "online":              validator_online,
                "last_heartbeat_utc":  last_heartbeat,
                "heartbeat_age_min":   hb_age_minutes,
                "heartbeat_detail":    heartbeat_detail,
                "active_feed":         active_feed,
            },
            "accuracy": {
                "total_validations":   total,
                "discrepancy_count":   disc_count,
                "discrepancy_rate_pct": disc_rate,
                "tp_mismatches":       tp_misses,
                "sl_mismatches":       sl_misses,
                "entry_mismatches":    en_misses,
                "last_event_at":       last_event_at,
            },
            "spread": spread_info,
            "recommendation": (
                "✅ System operating within acceptable parameters."
                if health == "HEALTHY" else
                "⚠️ Review discrepancy logs and check validator heartbeat."
                if health == "DEGRADED" else
                "🚨 Immediate attention required — high discrepancy or validator offline."
            ),
        }

    except Exception as e:
        logger.error(f"Error generating validation status: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 3 on-demand spread report (API gateway for analyze_spread_impact.py)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/validation-report")
async def get_validation_report(
    days: int = Query(default=14, ge=1, le=90),
    symbol: str = Query(default="EURUSD"),
):
    """
    On-demand Phase 3 Spread Impact Report via API.

    Exposes the SpreadAdjuster.analyze() output as a JSON endpoint
    so the frontend (System Logs tab) can display the buffer recommendation
    without needing local script access.
    """
    try:
        from quantix_core.engine.spread_adjuster import SpreadAdjuster
        from quantix_core.feeds import get_feed
        import os

        feed = get_feed(os.getenv("VALIDATOR_FEED", "binance_proxy"))
        adj  = SpreadAdjuster(db=db, feed=feed)
        report = adj.analyze(symbol=symbol, lookback_days=days)
        buf    = adj.get_buffer(symbol=symbol)

        return {
            "success": True,
            "report":  report,
            "current_buffer": buf,
        }
    except Exception as e:
        logger.error(f"Error generating validation report: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5.1 — Auto-Adjuster Report
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/auto-adjuster-report")
async def get_auto_adjuster_report(
    symbol: str = Query(default="EURUSD"),
    learn: bool = Query(default=False, description="Run a learn cycle first"),
):
    """
    Phase 5.1 Auto-Adjuster state report.

    Returns the current learned hour-risk matrix, ATR multiplier,
    and buffer recommendation for the given symbol.

    Set ?learn=true to trigger a synchronous learn cycle before reporting
    (adds ~300ms latency).
    """
    try:
        from quantix_core.engine.auto_adjuster import AutoAdjuster
        from quantix_core.feeds import get_feed
        import os

        feed = get_feed(os.getenv("VALIDATOR_FEED", "binance_proxy"))
        adj  = AutoAdjuster(db=db, feed=feed)

        if learn:
            learn_summary = adj.learn()
        else:
            learn_summary = None

        report = adj.get_learning_report()
        buf    = adj.get_buffer(symbol=symbol)

        return {
            "success":        True,
            "symbol":         symbol,
            "report":         report,
            "current_buffer": buf,
            "learn_ran":      learn,
            "learn_summary":  learn_summary,
        }
    except Exception as e:
        logger.error(f"Error generating auto-adjuster report: {e}")
        return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 5.3 — Multi-Broker Comparison
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/broker-comparison")
async def get_broker_comparison(
    symbol: str = Query(default="EURUSD"),
):
    """
    Phase 5.3 — Live spread comparison across all configured brokers.

    Returns per-broker bid/ask/spread and identifies best (tightest spread) broker.
    """
    try:
        from quantix_core.feeds.multi_broker_feed import MultiBrokerEngine
        engine   = MultiBrokerEngine()
        result   = engine.compare_spreads(symbol=symbol)
        avail    = engine.availability_summary()
        return {"success": True, "comparison": result, "adapters": avail}
    except Exception as e:
        logger.error(f"Error in broker comparison: {e}")
        return {"success": False, "error": str(e)}


import pydantic

class SignalCheckRequest(pydantic.BaseModel):
    signal_id:    str = "test"
    asset:        str = "EURUSD"
    direction:    str = "BUY"
    entry_price:  float = 1.0850

@router.post("/broker-signal-check")
async def post_broker_signal_check(req: SignalCheckRequest):
    """
    Phase 5.3 — Check signal entry against multiple brokers.

    Returns per-broker entry hit verdict + consensus + best broker recommendation.
    """
    try:
        from quantix_core.feeds.multi_broker_feed import MultiBrokerEngine
        engine = MultiBrokerEngine()
        result = engine.check_signal(req.dict())
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error in broker signal check: {e}")
        return {"success": False, "error": str(e)}

