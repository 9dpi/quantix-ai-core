
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def check_telemetry():
    print(f"Checking telemetry from {settings.TABLE_ANALYSIS_LOG}...")
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(10)\
            .execute()
        
        if not res.data:
            print("No telemetry found in database.")
            return

        print(f"Last 10 Analysis Cycles (UTC):")
        print("-" * 80)
        for entry in res.data:
            ts = entry.get('timestamp')
            conf = entry.get('release_confidence', entry.get('confidence', 0))
            status = entry.get('status')
            refinement = entry.get('refinement', entry.get('refinement_reason', 'N/A'))
            print(f"{ts} | Status: {status} | Confidence: {conf:.2f} | {refinement}")
        
    except Exception as e:
        print(f"Error checking telemetry: {e}")

if __name__ == "__main__":
    asyncio.run(check_telemetry())
