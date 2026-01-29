
import asyncio
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

async def purge_all_mock():
    print("🧹 PURGING ALL MOCK/TEST DATA FROM SUPABASE...")
    try:
        # 1. Clean fx_signals
        db.client.table(settings.TABLE_SIGNALS).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"✅ Supabase signals table cleaned.")
        
        # 2. Clean fx_analysis_log
        db.client.table(settings.TABLE_ANALYSIS_LOG).delete().neq("id", 0).execute()
        print(f"✅ Supabase analysis log cleaned.")

        # 3. Clean validation table if exists
        try:
            db.client.table(settings.TABLE_VALIDATION).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            print(f"✅ Validation table cleaned.")
        except:
            pass

        # 4. Clean local files
        base_dir = os.path.dirname(os.path.abspath(__file__))
        audit_path = os.path.join(base_dir, "heartbeat_audit.jsonl")
        learning_path = os.path.join(os.path.dirname(base_dir), "dashboard", "learning_data.json")
        
        for path in [audit_path, learning_path]:
            if os.path.exists(path):
                os.remove(path)
                print(f"✅ Local file removed: {path}")

    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(purge_all_mock())
