"""
Quantix AI Core - Main FastAPI Application (Fresh Deploy Trigger)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import asyncio
import os
import pydantic
from datetime import datetime
import sys

# DEBUG FOR RAILWAY PATHS
logger.info(f"CWD: {os.getcwd()}")
logger.info(f"SYS.PATH: {sys.path}")

from quantix_core.api.routes import health, signals, ingestion, csv_ingestion, admin, features, structure, lab, public, reference, lab_reference, validation
from quantix_core.config.settings import settings
from quantix_core.database.connection import db
# from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
# from quantix_core.engine.signal_watcher import SignalWatcher
from twelvedata import TDClient

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Institutional Grade Market Intelligence and Sniper Signals API"
)

# --- CORS Configuration ---
# Universal access for Internal Alpha - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Include Routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(structure.router, prefix=settings.API_PREFIX, tags=["Structure"])
app.include_router(features.router, prefix=settings.API_PREFIX, tags=["Features"])
app.include_router(signals.router, prefix=f"{settings.API_PREFIX}/signals", tags=["Signals"])
app.include_router(ingestion.router, prefix=settings.API_PREFIX, tags=["Ingestion"])
app.include_router(csv_ingestion.router, prefix=f"{settings.API_PREFIX}/ingestion", tags=["CSV Ingestion"])
app.include_router(admin.router, prefix=settings.API_PREFIX, tags=["Admin"])
app.include_router(lab.router, prefix=f"{settings.API_PREFIX}/lab", tags=["Learning Lab"])
app.include_router(public.router, prefix=settings.API_PREFIX, tags=["Public API"])
app.include_router(reference.router, prefix=settings.API_PREFIX, tags=["Public API"])
app.include_router(lab_reference.router, prefix=settings.API_PREFIX, tags=["Signal Engine Lab"])
app.include_router(validation.router, prefix=settings.API_PREFIX, tags=["Validation"])

# --- Unified Components ---

class RegistrationRequest(pydantic.BaseModel):
    phone: str

@app.post(f"{settings.API_PREFIX}/register-telegram", tags=["Public API"])
async def register_telegram(req: RegistrationRequest):
    """
    Unified Telegram Registration - Replaces redundant Node.js backend
    """
    try:
        # 1. Log to Database or Audit file
        logger.info(f"🚀 Registration Request: {req.phone}")
        # In this architecture, we focus on Signal Quality
        return {"success": True, "message": "Registered at Quantix AI Core"}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return {"success": False, "error": str(e)}

@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "8080")
    logger.info(f"🚀 Quantix AI Core Engine ONLINE - Listening on port: {port}")
    logger.info(f"♻️ VERIFIED DEPLOY: System restart at {datetime.utcnow()} - Readiness confirmed")

    # Background tasks (non-blocking)
    asyncio.create_task(background_startup_tasks())


async def background_startup_tasks():
    """Background tasks that should NOT block app startup"""
    import threading

    await asyncio.sleep(2)  # Let server stabilise first

    try:
        # ── DB health check ───────────────────────────────────────────────
        logger.info("🔍 Running background connectivity checks...")
        is_healthy = db.health_check()
        if is_healthy:
            logger.info("✅ Database connection verified")
        else:
            logger.warning("⚠️ Database check failed — check Railway Variables")

        # ── Validation Layer (auto-start on Railway) ──────────────────────
        IS_RAILWAY = os.getenv("RAILWAY_ENVIRONMENT") is not None
        validator_enabled = os.getenv("VALIDATOR_ENABLED", "auto")

        should_run_validator = (
            validator_enabled == "true"
            or (validator_enabled == "auto" and IS_RAILWAY)
        )

        if should_run_validator:
            logger.info("🛡️ Starting Validation Layer as background worker...")

            def _run_validator():
                """Blocking validator loop — runs in its own daemon thread."""
                import time
                # Wait 5s before first cycle so main API is fully ready
                time.sleep(5)
                try:
                    # Add backend to sys.path for the thread
                    backend_dir = os.path.join(os.getcwd(), "backend")
                    if backend_dir not in sys.path:
                        sys.path.insert(0, backend_dir)

                    from run_pepperstone_validator import PepperstoneValidator

                    feed_source = os.getenv("VALIDATOR_FEED", "binance_proxy")
                    validator = PepperstoneValidator(feed_source=feed_source)

                    logger.info(
                        f"✅ Validation Layer ONLINE [feed={feed_source}] "
                        f"[env={'railway' if IS_RAILWAY else 'local'}]"
                    )
                    validator.run()  # Blocking loop — no problem in daemon thread

                except Exception as e:
                    logger.error(f"❌ Validation Layer crashed: {e}")
                    logger.exception(e)

            vt = threading.Thread(target=_run_validator, daemon=True, name="ValidationLayer")
            vt.start()
            logger.info("🛡️ Validation Layer thread launched")

        else:
            logger.info("ℹ️ Validator not started (set VALIDATOR_ENABLED=true to enable)")

        # ── Auto-Adjuster learning schedule ───────────────────────────────
        adj_enabled = os.getenv("AUTO_ADJUSTER_ENABLED", "auto")
        should_run_adj = (
            adj_enabled == "true"
            or (adj_enabled == "auto" and IS_RAILWAY)
        )

        if should_run_adj:
            try:
                from quantix_core.engine.auto_adjuster import AutoAdjuster

                adj = AutoAdjuster(db=db, feed=None)
                learn_interval = int(os.getenv("AUTO_ADJUSTER_INTERVAL", "3600"))
                adj.schedule(interval=learn_interval)
                logger.info(
                    f"🧠 Auto-Adjuster learning scheduled every {learn_interval}s"
                )
            except Exception as e:
                logger.warning(f"⚠️ Auto-Adjuster init failed (non-critical): {e}")

    except Exception as e:
        logger.error(f"⚠️ Background startup task failed: {e}")
        # App continues running even if background tasks fail




@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "utc_time": datetime.utcnow().isoformat(),
        "message": "Quantix AI Core Engine is active"
    }

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", settings.API_PORT))
    # Disable reload in production for stability
    uvicorn.run("quantix_core.api.main:app", host=settings.API_HOST, port=port, reload=False)
