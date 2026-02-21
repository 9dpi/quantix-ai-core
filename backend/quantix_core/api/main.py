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
    asyncio.create_task(_startup_checks())


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


# --- Root ---
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
