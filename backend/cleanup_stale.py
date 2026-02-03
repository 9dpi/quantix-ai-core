
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

async def cleanup():
    # Cancel anything older than 2 hours that isn't CLOSED
    limit = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    
    # 1. Update PUBLISHED/ACTIVE signals
    res1 = db.client.table('fx_signals')\
        .update({'status': 'CLOSED', 'state': 'CANCELLED', 'result': 'CANCELLED'})\
        .in_('status', ['PUBLISHED', 'ACTIVE'])\
        .lt('generated_at', limit)\
        .execute()
    
    # 2. Update CANDIDATE/DETECTED signals (just to keep DB clean)
    res2 = db.client.table('fx_signals')\
        .update({'status': 'CLOSED', 'state': 'CANCELLED', 'result': 'CANCELLED'})\
        .in_('status', ['CANDIDATE', 'DETECTED'])\
        .lt('generated_at', limit)\
        .execute()
        
    print(f"Cleaned up {len(res1.data) + len(res2.data)} stale signals.")

if __name__ == "__main__":
    asyncio.run(cleanup())
