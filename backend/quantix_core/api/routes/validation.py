from fastapi import APIRouter
from quantix_core.database.connection import db
from loguru import logger

router = APIRouter()

@router.get("/validation-logs")
async def get_validation_logs(limit: int = 50):
    """
    Fetch validation logs from Supabase
    Used by Frontend to visualize Validator performance
    """
    try:
        # Fetch from validation_events table
        res = db.client.table("validation_events")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
            
        return {"success": True, "data": res.data}
        
    except Exception as e:
        logger.error(f"Error fetching validation logs: {e}")
        return {"success": False, "error": str(e)}

@router.get("/analysis-logs")
async def get_analysis_logs(limit: int = 20):
    """
    Fetch AI Heartbeat (Analysis) logs from Supabase
    Used by Frontend to show 'Thinking' activity
    """
    try:
        res = db.client.table("fx_analysis_log")\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(limit)\
            .execute()
            
        return {"success": True, "data": res.data}
    except Exception as e:
        logger.error(f"Error fetching analysis logs: {e}")
        return {"success": False, "error": str(e)}
