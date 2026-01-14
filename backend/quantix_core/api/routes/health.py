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

@router.get("/health/ping")
async def ping():
    """Lightweight ping endpoint for quick availability checks"""
    return {"ping": "pong"}
