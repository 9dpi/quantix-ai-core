
import asyncio
import os
from datetime import datetime, timezone
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def test_write():
    print("Testing manual write to Supabase...")
    signal_base = {
        "asset": "EURUSD",
        "direction": "BUY",
        "timeframe": "M15",
        "entry_low": 1.2000,
        "entry_high": 1.2002,
        "tp": 1.2020,
        "sl": 1.1985,
        "reward_risk_ratio": 1.33,
        "ai_confidence": 0.99,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy": "TEST_AUTO_PUSH",
        "status": "ACTIVE"
    }
    try:
        res = db.client.table(settings.TABLE_SIGNALS).insert(signal_base).execute()
        print(f"Success! Inserted Signal ID: {res.data[0]['id']}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_write())
