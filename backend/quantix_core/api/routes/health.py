from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter()

# Track startup time for uptime calculation
_startup_time = time.time()

@router.get("/health")
async def health():
    """
    Production-grade health check endpoint for monitoring & autoscaling.
    Returns comprehensive system status for Prometheus/Railway Metrics.
    """
    uptime_seconds = int(time.time() - _startup_time)
    
    return {
        "status": "ok",
        "engine": "quantix_ai_core",
        "version": "0.1.0",
        "uptime_sec": uptime_seconds,
        "time": datetime.utcnow().isoformat() + "Z"
    }

@router.get("/health/audit")
async def get_audit_log():
    """
    Returns the latest 20 heartbeat logs as proof of 24/7 operation.
    """
    try:
        import os
        if not os.path.exists("heartbeat_audit.jsonl"):
            return {"status": "running", "audit": []}
            
        with open("heartbeat_audit.jsonl", "r") as f:
            lines = f.readlines()
            # Return last 20 heartbeats
            log_entries = [line.strip() for line in lines[-20:]]
            return {
                "status": "online",
                "total_cycles": len(lines),
                "latest_heartbeats": log_entries
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/health/ping")
async def ping():
    """Lightweight ping endpoint for quick availability checks"""
    return {"ping": "pong"}


@router.get("/health/threads")
async def get_threads():
    """
    Returns all active background threads.
    Use this to confirm ValidationLayer and AutoAdjuster are running on Railway.
    """
    import threading, os
    threads = [
        {
            "name":    t.name,
            "alive":   t.is_alive(),
            "daemon":  t.daemon,
            "ident":   t.ident,
        }
        for t in threading.enumerate()
    ]
    validator_alive = any(t["name"] == "ValidationLayer" and t["alive"] for t in threads)
    adjuster_alive  = any("AutoAdjuster" in t["name"] and t["alive"] for t in threads)

    return {
        "validator_thread_alive":    validator_alive,
        "auto_adjuster_alive":       adjuster_alive,
        "railway_env":              os.getenv("RAILWAY_ENVIRONMENT"),
        "validator_enabled":        os.getenv("VALIDATOR_ENABLED", "auto"),
        "validator_feed":           os.getenv("VALIDATOR_FEED", "binance_proxy"),
        "threads":                  threads,
    }

