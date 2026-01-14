"""
Quantix AI Core - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn
import asyncio
import os

from api.routes import health, signals, ingestion, csv_ingestion, admin
from config.settings import settings
from database.connection import db

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
app.include_router(signals.router, prefix=settings.API_PREFIX, tags=["Signals"])
app.include_router(ingestion.router, prefix=settings.API_PREFIX, tags=["Ingestion"])
app.include_router(csv_ingestion.router, prefix=f"{settings.API_PREFIX}/ingestion", tags=["CSV Ingestion"])
app.include_router(admin.router, prefix=settings.API_PREFIX, tags=["Admin"])

@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "8000")
    logger.info(f"🚀 Quantix AI Core Engine ONLINE - Listening on port: {port}")
    
    # Chạy toàn bộ việc kiểm tra DB và nạp data vào luồng ngầm
    asyncio.create_task(background_startup_tasks())

async def background_startup_tasks():
    """Background tasks that should NOT block app startup"""
    try:
        await asyncio.sleep(1)  # Đợi server ổn định
        logger.info("🔍 Running background connectivity checks...")
        
        # Kiểm tra DB ngầm
        is_healthy = await db.health_check()
        if is_healthy:
            logger.info("✅ Database connection verified in background")
        else:
            logger.warning("⚠️ Database check failed - check your Railway Variables")
            
    except Exception as e:
        logger.error(f"⚠️ Background task failed (non-critical): {e}")
        # App continues running even if background tasks fail


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "mode": settings.QUANTIX_MODE
    }

if __name__ == "__main__":
    uvicorn.run("api.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
