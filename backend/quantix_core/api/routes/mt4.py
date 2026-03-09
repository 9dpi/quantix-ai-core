from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger
from datetime import datetime, timezone
import json
import os

from quantix_core.database.connection import db
from quantix_core.config.settings import settings

router = APIRouter()

# Simple security token matching
def verify_token(authorization: Optional[str] = Header(None)):
    expected_token = "Bearer DEMO_MT4_TOKEN_2026" # Hardcoded for Phase 1 local test
    if authorization != expected_token:
        logger.warning(f"Unauthorized MT4 access attempt: {authorization}")
        raise HTTPException(status_code=401, detail="Invalid API Token")
    return True

@router.get("/signals/pending")
async def get_pending_signals(authorized: bool = Depends(verify_token)):
    """EA calls this every 1 second to fetch new signals"""
    try:
        # --- PHASE 5 TEST MOCK ---
        # Temporarily return a mock signal to test PARTIAL_CLOSE
        import os
        if os.path.exists("d:/Automator_Prj/Quantix_AI_Core/backend/ENABLE_MOCK.txt"):
            return {
                "success": True,
                "count": 1,
                "signals": [{
                    "signal_id": "TEST-PARTIAL-888",
                    "strategy_id": "Quantix_v4_SMC",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": "PARTIAL_CLOSE",
                    "close_lots": 0.05,
                    "symbol": "EURUSD",
                    "order_type": "BUY",
                    "risk_usd": 50.0,
                    "sl_price": 1.04,
                    "tp_price": 1.06,
                    "max_slippage_pips": 2.0,
                    "max_spread_pips": 10.0,
                    "magic_number": 900900
                }]
            }
        # -------------------------
        
        # Fetch signals that are 'ACTIVE' (Waiting for entry or already hit)
        # We query for WAITING_FOR_ENTRY or ENTRY_HIT to ensure MT4 gets the latest actionable setups
        res = db.client.table("fx_signals")\
            .select("*")\
            .in_("state", ["WAITING_FOR_ENTRY", "ENTRY_HIT"])\
            .order("generated_at", desc=True)\
            .limit(5)\
            .execute()
        
        signals = res.data
        if getattr(res, "data", None) is None and isinstance(res, list): # Fallback for some supabase-py versions
             signals = res
             
        if not signals:
            return {"success": True, "count": 0, "signals": []}
            
        mt4_payloads = []
        for sig in signals:
            try:
                # Need signal_id. If missing in DB, skip it.
                # In continuous_analyzer we just added it to the dict, 
                # but did we add it to the Supabase schema insertion logic?
                # Actually, continuous_analyzer pushes `signal_base` values to `fx_signals`.
                # If `signal_id` column doesn't exist, we might get a Supabase error.
                # Let's extract it from metadata if possible, or fallback
                
                meta = sig.get("metadata", {})
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except:
                        meta = {}
                        
                signal_id = sig.get("id")
                
                # If no signal_id, we can't ensure idempotency, skip it.
                if not signal_id:
                    continue

                payload = {
                    "signal_id": str(signal_id),
                    "strategy_id": "Quantix_v4_SMC",
                    "timestamp": sig.get("generated_at"),
                    "action": meta.get("action", "EXECUTE_MARKET") if sig.get("asset") != "TEST_PARTIAL" else "PARTIAL_CLOSE",
                    "close_lots": meta.get("close_lots", 0.0) if sig.get("asset") != "TEST_PARTIAL" else 0.05,
                    "symbol": sig.get("asset", "EURUSD"),
                    "order_type": sig.get("direction", "SELL"),
                    "risk_usd": getattr(settings, "RISK_PER_TRADE_USD", 50.0),
                    "sl_price": sig.get("sl"),
                    "tp_price": sig.get("tp"),
                    "max_slippage_pips": 2.0,
                    "max_spread_pips": 1.5,
                    "magic_number": 900900
                }
                mt4_payloads.append(payload)
            except Exception as e:
                logger.error(f"Error parsing MT4 payload for {sig.get('id')}: {e}")
                
        return {
            "success": True,
            "count": len(mt4_payloads),
            "signals": mt4_payloads
        }
    except Exception as e:
        logger.error(f"MT4 Polling Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class MT4Callback(BaseModel):
    signal_id: str
    status: str
    ticket: Optional[int] = None
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    executed_price: Optional[float] = None
    executed_lots: Optional[float] = None

@router.post("/callback")
async def process_mt4_callback(payload: MT4Callback, authorized: bool = Depends(verify_token)):
    """EA POSTs back execution results or broker errors"""
    try:
        logger.info(f"MT4 Callback Received: {payload.dict()}")
        
        callback_data = payload.dict()
        callback_data["created_at"] = datetime.now(timezone.utc).isoformat()
        
        # Unified Telemetry Entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "MT4_CALLBACK",
            "price": payload.executed_price if payload.executed_price else 0.0,
            "direction": json.dumps(callback_data),
            "confidence": 1.0,
            "status": payload.status,
            "strength": payload.executed_lots if payload.executed_lots else 0.0
        }
        
        # 1. Insert into Supabase (Primary)
        try:
            db.client.table("fx_analysis_log").insert(log_entry).execute()
        except Exception as e:
            logger.warning(f"Could not insert callback into fx_analysis_log: {e}")
            
        # 2. Local Fallback (Relative path for Cloud compatibility)
        log_dir = "./logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            
        log_file = os.path.join(log_dir, "mt4_executions.json")
        
        logs = []
        if os.path.exists(log_file):
            try:
                with open(log_file, "r") as f:
                    content = f.read()
                    if content:
                        logs = json.loads(content)
            except:
                pass
        
        logs.insert(0, callback_data)
        logs = logs[:100]
        
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

        return {"success": True, "message": "Callback processed safely"}
    except Exception as e:
        logger.error(f"MT4 Callback Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions")
async def get_mt4_executions():
    """Fetch recent MT4 execution raw logs for the dashboard"""
    # 1. Try Supabase first (Cloud Native)
    try:
        res = db.client.table("fx_analysis_log")\
            .select("*")\
            .eq("asset", "MT4_CALLBACK")\
            .order("timestamp", desc=True)\
            .limit(50)\
            .execute()
        
        if res.data:
            refined_logs = []
            for entry in res.data:
                try:
                    raw_data = json.loads(entry["direction"])
                    refined_logs.append(raw_data)
                except:
                    pass
            return {"success": True, "executions": refined_logs}
    except Exception as e:
        logger.warning(f"Supabase execution fetch failed: {e}")

    # 2. Fallback to Local Log
    log_file = "./logs/mt4_executions.json"
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
            return {"success": True, "executions": logs}
        except:
            pass
    return {"success": True, "executions": []}
