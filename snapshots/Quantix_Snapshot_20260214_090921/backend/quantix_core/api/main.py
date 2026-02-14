"""
Quantix AI Core - Main FastAPI Application (Fresh Deploy Trigger)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import asyncio
import os
from datetime import datetime

from quantix_core.api.routes import health, signals, ingestion, csv_ingestion, admin, features, structure, lab, public, reference, lab_reference
from quantix_core.config.settings import settings
from quantix_core.database.connection import db
from quantix_core.engine.continuous_analyzer import ContinuousAnalyzer
from quantix_core.engine.signal_watcher import SignalWatcher
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
app.include_router(signals.router, prefix=settings.API_PREFIX, tags=["Signals"])
app.include_router(ingestion.router, prefix=settings.API_PREFIX, tags=["Ingestion"])
app.include_router(csv_ingestion.router, prefix=f"{settings.API_PREFIX}/ingestion", tags=["CSV Ingestion"])
app.include_router(admin.router, prefix=settings.API_PREFIX, tags=["Admin"])
app.include_router(lab.router, prefix=f"{settings.API_PREFIX}/lab", tags=["Learning Lab"])
app.include_router(public.router, prefix=settings.API_PREFIX, tags=["Public API"])
app.include_router(reference.router, prefix=settings.API_PREFIX, tags=["Public API"])
app.include_router(lab_reference.router, prefix=settings.API_PREFIX, tags=["Signal Engine Lab"])

@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "8080")  # Railway uses 8080 by default
    logger.info(f"🚀 Quantix AI Core Engine ONLINE - Listening on port: {port}")
    logger.info(f"♻️ FORCE DEPLOY: System restart triggered at {datetime.utcnow()}")
    
    # Chạy toàn bộ việc kiểm tra DB và nạp data vào luồng ngầm
    asyncio.create_task(background_startup_tasks())

async def background_startup_tasks():
    """Background tasks that should NOT block app startup"""
    try:
        await asyncio.sleep(1)  # Đợi server ổn định
        logger.info("🔍 Running background connectivity checks...")
        
        # Kiểm tra DB ngầm
        is_healthy = db.health_check()
        if is_healthy:
            logger.info("✅ Database connection verified in background")
        else:
            logger.warning("⚠️ Database check failed - check your Railway Variables")
            
        # 🛡️ ARCHITECTURE ENFORCEMENT
        logger.info("🛡️ DATA LAYER: READ ONLY MODE ACTIVE")
        logger.info("🚫 WORKER TASKS DECOUPLED: Please run analyzer and watcher as separate services.")
        
    except Exception as e:
        logger.error(f"⚠️ Background task failed (non-critical): {e}")
        # App continues running even if background tasks fail


@app.get("/")
async def root():
    try:
        db_status = "connected" if db.health_check() else "db_error"
    except:
        db_status = "db_unavailable"
        
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "database": db_status,
        "utc_time": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", settings.API_PORT))
    uvicorn.run("quantix_core.api.main:app", host=settings.API_HOST, port=port, reload=settings.DEBUG)
