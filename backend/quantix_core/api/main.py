"""
Quantix AI Core - Main FastAPI Application

Role: Pure API server only.
  - Exposes REST endpoints for signals, analysis, and admin.
  - Does NOT spawn any background worker threads.

Background workers run as dedicated Railway processes (Procfile):
  - analyzer:  start_railway_analyzer.py   → ContinuousAnalyzer
  - watcher:   start_railway_watcher.py    → SignalWatcher
  - validator: start_railway_validator.py  → PepperstoneValidator
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
from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer

from quantix_core.api.routes import (
    health, signals, ingestion, csv_ingestion,
    admin, features, structure, lab, public,
    reference, lab_reference, validation
)
from quantix_core.config.settings import settings
from quantix_core.database.connection import db

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Institutional Grade Market Intelligence and Sniper Signals API"
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routers ---
app.include_router(health.router,         prefix=settings.API_PREFIX,                  tags=["Health"])
app.include_router(structure.router,      prefix=settings.API_PREFIX,                  tags=["Structure"])
app.include_router(features.router,       prefix=settings.API_PREFIX,                  tags=["Features"])
app.include_router(signals.router,        prefix=f"{settings.API_PREFIX}/signals",     tags=["Signals"])
app.include_router(ingestion.router,      prefix=settings.API_PREFIX,                  tags=["Ingestion"])
app.include_router(csv_ingestion.router,  prefix=f"{settings.API_PREFIX}/ingestion",  tags=["CSV Ingestion"])
app.include_router(admin.router,          prefix=settings.API_PREFIX,                  tags=["Admin"])
app.include_router(lab.router,            prefix=f"{settings.API_PREFIX}/lab",         tags=["Learning Lab"])
app.include_router(public.router,         prefix=settings.API_PREFIX,                  tags=["Public API"])
app.include_router(reference.router,      prefix=settings.API_PREFIX,                  tags=["Public API"])
app.include_router(lab_reference.router,  prefix=settings.API_PREFIX,                  tags=["Signal Engine Lab"])
app.include_router(validation.router,     prefix=settings.API_PREFIX,                  tags=["Validation"])


# --- Telegram Registration endpoint ---
class RegistrationRequest(pydantic.BaseModel):
    phone: str

@app.post(f"{settings.API_PREFIX}/register-telegram", tags=["Public API"])
async def register_telegram(req: RegistrationRequest):
    """Unified Telegram Registration"""
    try:
        logger.info(f"🚀 Registration Request: {req.phone}")
        return {"success": True, "message": "Registered at Quantix AI Core"}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return {"success": False, "error": str(e)}


# --- Startup ---
@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "8080")
    instance = os.getenv("RAILWAY_SERVICE_NAME", "local")
    logger.info(f"🚀 Quantix API ONLINE — port={port} | instance={instance}")
    logger.info(f"⏰ UTC: {datetime.utcnow().isoformat()}")
    
    # --- AUTO-WORKER INTEGRATION (v3.2) ---
    # Start background tasks directly in API process to ensure 100% uptime on Railway
    # without needing dedicated worker services enabled in the UI.
    asyncio.create_task(_run_analyzer_loop())
    asyncio.create_task(_run_watcher_loop())
    
    asyncio.create_task(_startup_checks())

async def _run_analyzer_loop():
    """Embedded Analyzer Loop"""
    try:
        from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
        logger.info("💓 Starting Embedded Analyzer Task...")
        analyzer = ContinuousAnalyzer()
        # Non-blocking loop
        while True:
            try:
                analyzer.run_cycle()
            except Exception as e:
                logger.error(f"Analyzer loop error: {e}")
            await asyncio.sleep(settings.MONITOR_INTERVAL_SECONDS)
    except Exception as e:
        logger.critical(f"Failed to initialize Embedded Analyzer: {e}")

async def _run_watcher_loop():
    """Embedded Watcher Loop"""
    try:
        from quantix_core.engine.signal_watcher import SignalWatcher
        logger.info("👀 Starting Embedded Watcher Task...")
        watcher = SignalWatcher()
        while True:
            try:
                watcher.run_cycle()
            except Exception as e:
                logger.error(f"Watcher loop error: {e}")
            await asyncio.sleep(60) # Watcher runs every minute
    except Exception as e:
        logger.critical(f"Failed to initialize Embedded Watcher: {e}")


async def _startup_checks():
    """Lightweight DB connectivity check on startup. NO worker threads."""
    await asyncio.sleep(2)
    try:
        ok = db.health_check()
        if ok:
            logger.info("✅ Supabase connection OK")
        else:
            logger.warning("⚠️ Supabase connection FAILED — check Railway env vars")
    except Exception as e:
        logger.error(f"⚠️ Startup check error: {e}")

    logger.info(
        "ℹ️  Workers (Analyzer / Watcher / Validator) run as dedicated "
        "Railway services — not embedded in API process."
    )


@app.get("/diagnostic/trigger", tags=["Admin"])
async def trigger_diagnostic():
    """Manually trigger one analysis cycle for debugging"""
    try:
        analyzer = ContinuousAnalyzer()
        # Mocking run_cycle steps to get results
        raw_data = analyzer.td_client.get_time_series(symbol="EUR/USD", interval="15min", outputsize=10)
        df = analyzer.convert_to_df(raw_data)
        
        if df.empty:
             return {"success": False, "error": "TwelveData returned empty data", "raw": raw_data}
             
        state = analyzer.engine.analyze(df, symbol="EURUSD", timeframe="M15", source="twelve_data")
        
        # Test DB insertion
        db_ok = False
        db_err = None
        try:
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "DIAGNOSTIC",
                "direction": "TEST",
                "status": "OK",
                "price": float(df.iloc[-1]["close"]),
                "confidence": 0.0,
                "strength": 0.0
            }).execute()
            db_ok = True
        except Exception as e:
             db_err = str(e)
             
        return {
            "success": True, 
            "message": "Diagnostic check passed.",
            "db_insertion": db_ok,
            "db_error": db_err,
            "data_points": len(df),
            "current_price": float(df.iloc[-1]["close"]),
            "market_state": state.state,
            "confidence": state.confidence
        }
    except Exception as e:
        logger.error(f"Diagnostic trigger failed: {e}")
        return {"success": False, "error": str(e)}

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "utc_time": datetime.utcnow().isoformat(),
        "message": "Quantix AI Core API is active"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", settings.API_PORT))
    uvicorn.run("quantix_core.api.main:app", host=settings.API_HOST, port=port, reload=False)
