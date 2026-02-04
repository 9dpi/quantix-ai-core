
import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def recovery():
    print("🚀 STARTING PRODUCTION RECOVERY (SAFE MODE)...")
    
    # 1. Clear Stuck Published/EntryHit signals
    print("Step 1: Expiring stuck active signals...")
    stuck_res = db.client.table(settings.TABLE_SIGNALS)\
        .select("id, state, status, generated_at")\
        .in_("status", ["PUBLISHED", "ENTRY_HIT"])\
        .execute()
    
    if stuck_res.data:
        for sig in stuck_res.data:
            print(f"  - Expiring: {sig['id']} ({sig['state']})")
            # Use .select("id") to prevent SDK from fetching missing columns
            db.client.table(settings.TABLE_SIGNALS).update({
                "state": "EXPIRED",
                "status": "CLOSED",
                "result": "STUCK_RECOVERY",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", sig["id"]).select("id").execute()
        print(f"✅ Success! Recovered {len(stuck_res.data)} stuck signals.")
    else:
        print("  - No stuck active signals found.")

    # 2. Nuke Zombies (WAITING_FOR_ENTRY with no TG ID)
    print("\nStep 2: Nuking zombies...")
    zombies_res = db.client.table(settings.TABLE_SIGNALS)\
        .select("id")\
        .eq("state", "WAITING_FOR_ENTRY")\
        .is_("telegram_message_id", "null")\
        .execute()
    
    if zombies_res.data:
        zombie_ids = [z['id'] for z in zombies_res.data]
        print(f"  - Found {len(zombie_ids)} zombies. Cleaning up in chunks...")
        
        chunk_size = 50
        count = 0
        for i in range(0, len(zombie_ids), chunk_size):
            chunk = zombie_ids[i:i + chunk_size]
            db.client.table(settings.TABLE_SIGNALS).update({
                "state": "CANCELLED",
                "status": "CLOSED",
                "result": "CANCELLED_ZOMBIE_RECOVERY",
                "closed_at": datetime.now(timezone.utc).isoformat()
            }).in_("id", chunk).select("id").execute()
            count += len(chunk)
        print(f"✅ Success! Nuked {count} zombies.")
    else:
        print("  - No zombies found.")

    print("\n🏁 RECOVERY COMPLETE. System should be unlocked now.")

if __name__ == "__main__":
    asyncio.run(recovery())
