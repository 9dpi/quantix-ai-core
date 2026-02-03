
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from loguru import logger

async def check_last_24h():
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).isoformat()
    
    logger.info(f"Checking system activity since {day_ago}")
    
    try:
        # 1. Total Scans (Heartbeats)
        scans_res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("timestamp", count="exact")\
            .gte("timestamp", day_ago)\
            .execute()
        total_scans = scans_res.count if scans_res else 0
        
        # 2. Total Signals Generated
        sigs_res = db.client.table(settings.TABLE_SIGNALS)\
            .select("*", count="exact")\
            .gte("generated_at", day_ago)\
            .order("generated_at", desc=True)\
            .execute()
        total_sigs = sigs_res.count if sigs_res else 0
        signals = sigs_res.data if sigs_res else []
        
        # 3. Outcomes Breakdown
        outcomes = {
            "WAITING_FOR_ENTRY": 0,
            "ENTRY_HIT": 0,
            "TP_HIT": 0,
            "SL_HIT": 0,
            "CANCELLED": 0
        }
        released_count = 0
        
        for sig in signals:
            state = sig.get("state")
            if state in outcomes:
                outcomes[state] += 1
            if sig.get("telegram_message_id"):
                released_count += 1
        
        # 4. Report
        print("\n" + "="*50)
        print(f"📊 SYSTEM REPORT (LAST 24 HOURS)")
        print("="*50)
        print(f"Total Market Scans:    {total_scans}")
        print(f"Total Setups Found:    {total_sigs}")
        print(f"Publicly Released:     {released_count}")
        print("-" * 30)
        print(f"Current States:")
        for state, count in outcomes.items():
            print(f"  • {state:18}: {count}")
        
        if signals:
            print("-" * 30)
            print("Recent Signals:")
            for s in signals[:5]:
                print(f"  [{s['generated_at'][11:16]}] {s['asset']} {s['direction']} | {s['state']} | Conf: {s['ai_confidence']:.2f}")
        
        print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Failed to check activity: {e}")

if __name__ == "__main__":
    asyncio.run(check_last_24h())
