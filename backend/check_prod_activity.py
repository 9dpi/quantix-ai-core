
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone

async def check_production_activity():
    print("Checking Database for Production Activity (Railway Instance)...")
    
    # Check for recent signals
    try:
        res = db.client.table('fx_signals').select('*').order('generated_at', desc=True).limit(5).execute()
        if res.data:
            print("\n--- Recent Signals Found ---")
            for s in res.data:
                print(f"ID: {s.get('id')} | Asset: {s.get('asset')} | Status: {s.get('status')} | State: {s.get('state')} | Generated At: {s.get('generated_at')}")
        else:
            print("\nNo signals found in database.")
    except Exception as e:
        print(f"Error checking signals: {e}")

    # Check for recent analysis logs (Heartbeats)
    try:
        res = db.client.table('fx_analysis_log').select('*').order('timestamp', desc=True).limit(5).execute()
        if res.data:
            print("\n--- Recent Analysis Heartbeats ---")
            for log in res.data:
                print(f"Time: {log.get('timestamp')} | Status: {log.get('status')} | Direction: {log.get('direction')} | Conf: {log.get('confidence')}")
        else:
            print("\nNo analysis logs found.")
    except Exception as e:
        print(f"Error checking analysis logs: {e}")

if __name__ == "__main__":
    asyncio.run(check_production_activity())
