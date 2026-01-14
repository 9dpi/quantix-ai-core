"""
Database Inspection Endpoint
GET /api/v1/admin/inspect-db
"""

from fastapi import APIRouter
from backend.database.supabase_client import get_supabase_client

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/inspect-db")
async def inspect_database():
    """
    Inspect database to check if Quantix has data to learn from.
    
    Returns summary of:
    - Raw candles
    - Validated candles (learning set)
    - Ingestion history
    - v3.2 learning tables status
    """
    
    db = get_supabase_client()
    
    summary = {
        "status": "success",
        "timestamp": "2026-01-14T20:21:00Z",
        "checks": {}
    }
    
    # Check 1: Raw candles
    try:
        result = db.table('raw_candles').select('*', count='exact').limit(5).execute()
        summary["checks"]["raw_candles"] = {
            "exists": True,
            "total_count": result.count if hasattr(result, 'count') else len(result.data),
            "sample": result.data[:3] if result.data else []
        }
    except Exception as e:
        summary["checks"]["raw_candles"] = {
            "exists": False,
            "error": str(e)
        }
    
    # Check 2: Validated candles (learning set)
    try:
        result = db.table('validated_candles').select('*', count='exact').limit(5).execute()
        summary["checks"]["validated_candles"] = {
            "exists": True,
            "total_count": result.count if hasattr(result, 'count') else len(result.data),
            "sample": result.data[:3] if result.data else [],
            "learning_ready": (result.count if hasattr(result, 'count') else len(result.data)) > 0
        }
    except Exception as e:
        summary["checks"]["validated_candles"] = {
            "exists": False,
            "error": str(e),
            "learning_ready": False
        }
    
    # Check 3: Ingestion audit
    try:
        result = db.table('ingestion_audit_log').select('*').order('ingested_at', desc=True).limit(5).execute()
        summary["checks"]["ingestion_audit"] = {
            "exists": True,
            "total_count": len(result.data),
            "recent": result.data[:3] if result.data else []
        }
    except Exception as e:
        summary["checks"]["ingestion_audit"] = {
            "exists": False,
            "error": str(e)
        }
    
    # Check 4: v3.2 Learning tables
    v32_tables = {}
    
    for table_name in ['market_candles_clean', 'signal_outcomes', 'learning_memory']:
        try:
            result = db.table(table_name).select('*', count='exact').limit(1).execute()
            v32_tables[table_name] = {
                "deployed": True,
                "count": result.count if hasattr(result, 'count') else 0
            }
        except Exception as e:
            v32_tables[table_name] = {
                "deployed": False,
                "error": str(e)[:100]
            }
    
    summary["checks"]["v32_learning_schema"] = v32_tables
    
    # Summary assessment
    validated_count = summary["checks"].get("validated_candles", {}).get("total_count", 0)
    v32_deployed = all(t.get("deployed", False) for t in v32_tables.values())
    
    summary["assessment"] = {
        "has_learning_data": validated_count > 0,
        "validated_candles_count": validated_count,
        "v32_schema_deployed": v32_deployed,
        "ready_for_learning": validated_count > 0 and v32_deployed,
        "next_steps": []
    }
    
    if validated_count == 0:
        summary["assessment"]["next_steps"].append("Upload CSV data via Ingestion Portal")
    
    if not v32_deployed:
        summary["assessment"]["next_steps"].append("Deploy v3.2 schema: supabase/006_continuous_learning_schema.sql")
    
    if validated_count > 0 and v32_deployed:
        summary["assessment"]["next_steps"].append("System ready - Begin signal generation and learning")
    
    return summary
