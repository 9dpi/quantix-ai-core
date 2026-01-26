import asyncio
import sys
import os

# Add backend to path
sys.path.append('d:/Automator_Prj/Quantix_AI_Core/backend')

from quantix_core.database.connection import db

async def check():
    try:
        # Check total signals
        res = await db.fetch("SELECT count(*) as total FROM fx_signals")
        print(f"TOTAL_SIGNALS: {res}")
        
        # Check latest 3
        latest = await db.fetch("SELECT id, status, generated_at FROM fx_signals ORDER BY generated_at DESC LIMIT 3")
        print(f"LATEST_3: {latest}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check())
