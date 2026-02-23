
import asyncio
import os
from datetime import datetime, timezone
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from loguru import logger

async def expire_old():
    logger.info("🧹 Starting robust signal cleanup...")
    now = datetime.now(timezone.utc)
    
    try:
        # 1. Fetch all potentially stuck signals
        res = db.client.table(settings.TABLE_SIGNALS).select("*").in_(
            "state", ["WAITING_FOR_ENTRY", "ENTRY_HIT", "ACTIVE", "PUBLISHED"]
        ).execute()
        
        signals = res.data or []
        expired_count = 0
        
        for sig in signals:
            sig_id = sig.get("id")
            state = sig.get("state")
            gen_at_str = sig.get("generated_at")
            hit_at_str = sig.get("entry_hit_at")
            
            if not gen_at_str: continue
            gen_at = datetime.fromisoformat(gen_at_str.replace("Z", "+00:00"))
            
            is_expired = False
            reason = ""
            
            # WAITING -> CANCELLED (35m)
            if state in ["WAITING_FOR_ENTRY", "PUBLISHED"]:
                age_min = (now - gen_at).total_seconds() / 60
                if age_min >= settings.MAX_PENDING_DURATION_MINUTES:
                    is_expired = True
                    reason = f"Entry window expired ({int(age_min)}m > {settings.MAX_PENDING_DURATION_MINUTES}m)"
            
            # ACTIVE -> TIME_EXIT (90m)
            elif state in ["ENTRY_HIT", "ACTIVE"]:
                start_time = gen_at
                if hit_at_str:
                    start_time = datetime.fromisoformat(hit_at_str.replace("Z", "+00:00"))
                
                age_min = (now - start_time).total_seconds() / 60
                if age_min >= settings.MAX_TRADE_DURATION_MINUTES:
                    is_expired = True
                    reason = f"Trade duration reached ({int(age_min)}m > {settings.MAX_TRADE_DURATION_MINUTES}m)"
            
            if is_expired:
                logger.warning(f"⚠️ Expiring Signal {sig_id}: {reason}")
                db.client.table(settings.TABLE_SIGNALS).update({
                    "state": "CANCELLED" if state in ["WAITING_FOR_ENTRY", "PUBLISHED"] else "TIME_EXIT",
                    "status": "EXPIRED" if state in ["WAITING_FOR_ENTRY", "PUBLISHED"] else "CLOSED_TIMEOUT",
                    "result": "CANCELLED",
                    "closed_at": now.isoformat()
                }).eq("id", sig_id).execute()
                expired_count += 1

        logger.success(f"✅ Cleanup finished. Expired {expired_count} stuck signals.")
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

if __name__ == "__main__":
    asyncio.run(expire_old())
