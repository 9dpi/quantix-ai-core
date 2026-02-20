"""
monitor_validation.py — Phase 4.3 Production Monitor
=====================================================
Lightweight continuous monitoring daemon for the validation layer.

Runs as a separate process and performs daily checks:
  - Validator heartbeat freshness
  - Discrepancy rate drift
  - Alerts via Telegram if thresholds exceeded
  - Writes monitoring_report.json for quick inspection

Usage:
    # Run monitor (checks every 30 minutes)
    python backend/monitor_validation.py

    # One-shot check (print and exit)
    python backend/monitor_validation.py --once

    # Custom interval
    python backend/monitor_validation.py --interval 600  # every 10 minutes

    # Disable Telegram alerts (local dev)
    python backend/monitor_validation.py --no-telegram
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

API_BASE = os.getenv(
    "QUANTIX_API_URL",
    "https://quantixaicore-production.up.railway.app/api/v1"
)

THRESHOLDS = {
    "max_disc_pct":          5.0,    # Alert if discrepancy rate exceeds this
    "max_hb_age_min":       15.0,    # Alert if validator offline > 15 min
    "min_validations_7d":    5,      # Warn if too few validations (validator may be stuck)
}

REPORT_FILE = Path(__file__).parent / "monitoring_report.json"


# ─────────────────────────────────────────────────────────────────────────────
# Monitor
# ─────────────────────────────────────────────────────────────────────────────

class ValidationMonitor:

    def __init__(self, enable_telegram: bool = True):
        self.enable_telegram = enable_telegram
        self._telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._admin_chat_id  = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "7985984228")

    def fetch_status(self, days: int = 7) -> dict:
        """Hit the production /validation-status endpoint."""
        try:
            resp = requests.get(
                f"{API_BASE}/validation-status",
                params={"days": days},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.error(f"Failed to fetch validation-status: {e}")
        return {}

    def evaluate(self, status: dict) -> list:
        """
        Compare status against thresholds.
        Returns list of alert messages (empty = all good).
        """
        alerts = []

        if not status.get("success"):
            alerts.append("🚨 /validation-status API returned an error")
            return alerts

        health = status.get("health", "UNKNOWN")
        acc    = status.get("accuracy", {})
        val    = status.get("validator", {})

        disc_rate  = acc.get("discrepancy_rate_pct", 0.0)
        hb_age     = val.get("heartbeat_age_min")
        total_val  = acc.get("total_validations", 0)
        online     = val.get("online", False)

        if not online:
            alerts.append(
                f"⚠️ Validator is OFFLINE — "
                f"last heartbeat {hb_age or '?'} min ago"
            )

        if hb_age is not None and hb_age > THRESHOLDS["max_hb_age_min"]:
            alerts.append(
                f"⚠️ Heartbeat stale: {hb_age:.1f} min "
                f"(threshold: {THRESHOLDS['max_hb_age_min']} min)"
            )

        if disc_rate > THRESHOLDS["max_disc_pct"]:
            alerts.append(
                f"🚨 Discrepancy rate HIGH: {disc_rate:.2f}% "
                f"(threshold: {THRESHOLDS['max_disc_pct']}%)"
            )

        if total_val < THRESHOLDS["min_validations_7d"]:
            alerts.append(
                f"⚠️ Low validation volume: {total_val} events in 7 days "
                f"(min: {THRESHOLDS['min_validations_7d']})"
            )

        return alerts

    def run_once(self) -> bool:
        """Single monitoring check. Returns True if healthy."""
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        status  = self.fetch_status()
        alerts  = self.evaluate(status)

        health = status.get("health", "UNKNOWN")
        acc    = status.get("accuracy", {})
        val    = status.get("validator", {})

        # Summary line
        disc_rate = acc.get("discrepancy_rate_pct", "?")
        total_val = acc.get("total_validations",     "?")
        hb_age    = val.get("heartbeat_age_min",     "?")
        feed      = val.get("active_feed",           "?")

        logger.info(
            f"[Monitor] {now_str} | "
            f"health={health} | "
            f"disc={disc_rate}% | "
            f"total={total_val} | "
            f"hb_age={hb_age}min | "
            f"feed={feed}"
        )

        # Save report snapshot
        report = {
            "checked_at":    now_str,
            "health":        health,
            "alerts":        alerts,
            "status_snapshot": status,
        }
        try:
            with open(REPORT_FILE, "w") as f:
                json.dump(report, f, indent=2)
        except Exception:
            pass

        # Send Telegram alert if needed
        if alerts:
            msg_lines = [
                f"🔔 *Quantix Validation Monitor*",
                f"📅 {now_str}",
                f"",
            ] + alerts + [
                f"",
                f"System health: *{health}*",
                f"Disc rate: {disc_rate}%  |  Events: {total_val}",
                f"HB age: {hb_age} min  |  Feed: {feed}",
            ]
            self._send_telegram("\n".join(msg_lines))

        return len(alerts) == 0

    def _send_telegram(self, message: str):
        if not self.enable_telegram or not self._telegram_token:
            logger.warning(f"[Monitor] Telegram disabled or token missing. Alert:\n{message}")
            return
        try:
            url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
            payload = {
                "chat_id":    self._admin_chat_id,
                "text":       message,
                "parse_mode": "Markdown",
            }
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                logger.success("[Monitor] Alert sent to Telegram admin")
            else:
                logger.warning(f"[Monitor] Telegram send failed: HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"[Monitor] Telegram error: {e}")

    def run_loop(self, interval_seconds: int = 1800):
        """Continuous monitoring loop (default: every 30 minutes)."""
        logger.info(
            f"🟢 Validation Monitor started "
            f"(interval={interval_seconds}s, telegram={'ON' if self.enable_telegram else 'OFF'})"
        )
        while True:
            try:
                healthy = self.run_once()
                status  = "✅ Healthy" if healthy else "⚠️  Issues detected"
                logger.info(f"[Monitor] Cycle complete → {status}. Next in {interval_seconds}s.")
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user.")
                break
            except Exception as e:
                logger.error(f"[Monitor] Unexpected error: {e}")
            time.sleep(interval_seconds)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Phase 4.3 Validation Production Monitor")
    p.add_argument("--once",        action="store_true",
                   help="Run a single check and exit")
    p.add_argument("--interval",    type=int,  default=1800,
                   help="Check interval in seconds (default: 1800 = 30 min)")
    p.add_argument("--no-telegram", action="store_true",
                   help="Disable Telegram alerts")
    args = p.parse_args()

    monitor = ValidationMonitor(enable_telegram=not args.no_telegram)

    if args.once:
        ok = monitor.run_once()
        sys.exit(0 if ok else 1)
    else:
        monitor.run_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
