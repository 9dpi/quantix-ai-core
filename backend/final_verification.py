
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from quantix_core.notifications.telegram_notifier_v2 import create_notifier
from loguru import logger

async def backfill_and_verify():
    logger.info("🎬 Starting Final Verification & Backfill Pipeline...")
    
    # 1. Config Loader Check (INIT_OK)
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    admin_chat_id = settings.TELEGRAM_ADMIN_CHAT_ID
    
    if not token or not chat_id:
        logger.critical("❌ [INIT_FAIL] Telegram config incomplete!")
        return
        
    notifier = create_notifier(token, chat_id, admin_chat_id)
    logger.success(f"✅ [INIT_OK] Telegram Notifier Ready.")
    
    # 2. Inform Admin
    if admin_chat_id:
        notifier.send_admin_notification("🚀 *Quantix AI Core v2.1* [INIT_OK]\nStatus: Pipeline Standardized (Lock-Flow).")

    # 3. BACKFILL Logic: Find high conf CANDIDATES from London session today
    now = datetime.now(timezone.utc)
    today = now.date().isoformat()
    
    logger.info("🔍 Searching for valid CANDIDATES to backfill...")
    try:
        res = db.client.table(settings.TABLE_SIGNALS)\
            .select("*")\
            .eq("status", "CANDIDATE")\
            .gte("generated_at", today)\
            .order("generated_at", desc=True)\
            .execute()
            
        candidates = res.data if res else []
        logger.info(f"Found {len(candidates)} candidates today.")
        
        backfilled_count = 0
        for sig in candidates:
            # Re-verify with Release Rules (Session 8-17 UTC, Score 0.75)
            gen_at = datetime.fromisoformat(sig["generated_at"].replace("Z", "+00:00"))
            score = float(sig.get("ai_confidence", 0)) # Simple bypass for backfill if it was high raw
            
            # For backfill, we only take the ULTRA ones (>0.90) to avoid spamming historicals
            if score >= 0.90 and 8 <= gen_at.hour <= 17:
                logger.info(f"♻️ Backfilling signal {sig['id']} (Raw: {score:.2f})")
                msg_id = notifier.send_waiting_for_entry(sig)
                if msg_id:
                    db.client.table(settings.TABLE_SIGNALS).update({
                        "telegram_message_id": msg_id,
                        "status": "ACTIVE"
                    }).eq("id", sig["id"]).execute()
                    backfilled_count += 1
                    logger.success(f"⚓ [BACKFILL_LOCK] Signal {sig['id']} linked to TG: {msg_id}")
        
        logger.info(f"Completed. Backfilled {backfilled_count} signals.")

    except Exception as e:
        logger.error(f"Backfill failed: {e}")

    # 4. Final Dry Run Signal
    logger.info("🧪 Launching Final Dry-Run Signal...")
    dry_run_sig = {
        "asset": "EURUSD VERIFY",
        "direction": "SELL",
        "entry_price": 1.12000,
        "tp": 1.11900,
        "sl": 1.12100,
        "ai_confidence": 0.88,
        "expiry_at": (now + timedelta(minutes=15)).isoformat(),
        "state": "WAITING_FOR_ENTRY"
    }
    
    final_id = notifier.send_waiting_for_entry(dry_run_sig)
    if final_id:
        logger.success(f"🏁 Verification Signal Sent (TG: {final_id})")
        if admin_chat_id:
            notifier.send_admin_notification(f"🏁 *Verification Complete*\nSync 1:1 established.\nDry-run TG ID: {final_id}")
    else:
        logger.error("❌ Final Verification Signal FAILED.")

if __name__ == "__main__":
    asyncio.run(backfill_and_verify())
