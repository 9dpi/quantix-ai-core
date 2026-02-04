
import asyncio
import json
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def check_detailed_telemetry():
    try:
        res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(5)\
            .execute()
        
        print(f"Detailed Analysis Logs:")
        print("-" * 100)
        for data in res.data:
            print(json.dumps(data, indent=2))
            print("-" * 100)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_detailed_telemetry())
