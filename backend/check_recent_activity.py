
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from loguru import logger

async def check_recent_activity(days=5):
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).isoformat()
    
    logger.info(f"Checking system activity since {since} ({days} days ago)")
    
    try:
        # 1. Total Signals Generated
        sigs_res = db.client.table(settings.TABLE_SIGNALS)\
            .select("*", count="exact")\
            .gte("generated_at", since)\
            .order("generated_at", desc=True)\
            .execute()
        total_sigs = sigs_res.count if sigs_res else 0
        signals = sigs_res.data if sigs_res else []
        
        print("\n" + "="*50)
        print(f"📊 RECENT ACTIVITY REPORT (LAST {days} DAYS)")
        print("="*50)
        print(f"Total Setups Found:    {total_sigs}")
        
        if signals:
            print("-" * 30)
            print("Recent Signals:")
            for s in signals[:10]:
                ts = s['generated_at'][0:16].replace('T', ' ')
                tg_id = "YES" if s.get('telegram_message_id') else "NO"
                print(f"  [{ts}] {s['asset']} {s['direction']} | {s['state']} | Released: {tg_id} | Conf: {s['ai_confidence']:.2f}")
        else:
            print("No signals found in the last 5 days.")
        
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Failed to check activity: {e}")

if __name__ == "__main__":
    asyncio.run(check_recent_activity())
