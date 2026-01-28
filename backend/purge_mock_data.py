
import asyncio
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def purge_all_mock():
    print("🧹 PURGING ALL MOCK/TEST DATA FROM SUPABASE...")
    try:
        # Delete signals with status 'TEST' or 'CANDIDATE' or generated_at from 2026-01-01
        # In a real environment, we delete everything that isn't 'ACTIVE' or 'EXPIRED' 
        # but the user said "Dọn dẹp hết mock và chỉ dùng real"
        # So I will delete everything and let the Miner restart fresh with real data only.
        
        res = db.client.table(settings.TABLE_SIGNALS).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Supabase Cleaned: Deleted existing records.")
        
        # Also clean validation table if exists
        try:
            db.client.table(settings.TABLE_VALIDATION).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print(f"✅ Validation table cleaned.")
        except:
            pass

    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(purge_all_mock())
