"""
Quantix AI Core - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

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
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    # Optional: Basic DB connectivity check
    is_healthy = await db.health_check()
    if is_healthy:
        logger.info("✅ Database connection verified")
        # --- AUTO-SEED DATA ---
        try:
            await seed_data()
        except Exception as e:
            logger.error(f"❌ Auto-seeding failed: {e}")
    else:
        logger.warning("⚠️ Database connection check failed - ensure SUPABASE keys are correct")

async def seed_data():
    import os
    from ingestion.pipeline import CSVIngestionPipeline
    from api.routes.csv_ingestion import _log_ingestion_audit
    
    # In Docker, the path will be 'data' because we copied backend/ to /app/
    data_dir = "data"
    if not os.path.exists(data_dir):
        logger.info(f"📁 Seed directory '{data_dir}' not found, skipping auto-seed.")
        return
        
    pipeline = CSVIngestionPipeline()
    files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not files:
        return
        
    logger.info(f"🌱 Auto-seeding found {len(files)} files: {files}")
    for filename in files:
        try:
            path = os.path.join(data_dir, filename)
            asset = filename.split('_')[0].upper()
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            result = await pipeline.ingest_csv_content(
                content, 
                asset=asset, 
                timeframe="D1",
                source="auto_seed"
            )
            
            if result['status'] == 'success':
                await _log_ingestion_audit(result, asset=asset, timeframe="D1")
                logger.info(f"✅ Auto-seeded: {filename}")
        except Exception as e:
            logger.error(f"⚠️ Failed to seed {filename}: {e}")

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
