
import asyncio
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
from datetime import datetime, timezone

async def revalidate_system():
    print("🛡️ STARTING SYSTEM RE-VALIDATION (Target: Clean Ledger)")
    
    try:
        # 1. Identity unreleased or mock signals
        # Logic: KEEP if telegram_message_id is not null AND asset is real
        # DELETE everything else
        
        print("📊 Counting current data state...")
        total_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").execute()
        total_count = total_res.count if total_res else 0
        
        released_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").not_.is_("telegram_message_id", "null").execute()
        released_count = released_res.count if released_res else 0
        
        to_purge_count = total_count - released_count
        
        print(f"• Total Data Points: {total_count}")
        print(f"• Released Signals (Proof Anchored): {released_count}")
        print(f"• To be Purged (Mock/Old logic/Unreleased): {to_purge_count}")
        
        if to_purge_count > 0:
            print(f"🧹 Purging {to_purge_count} unvalidated records...")
            # Delete signals where telegram_message_id is null
            db.client.table(settings.TABLE_SIGNALS).delete().is_("telegram_message_id", "null").execute()
            print("✅ Purge complete. Signals table is now a Clean Ledger.")
        else:
            print("✨ System already clean. No purge needed.")
            
        # 2. Reset Analysis Log for fresh start of the new pipeline
        print("🚿 Clearing old analysis logs...")
        db.client.table(settings.TABLE_ANALYSIS_LOG).delete().neq("id", 0).execute()
        print("✅ Analysis logs cleared.")
        
        # 3. Clean local audit files
        base_dir = os.path.dirname(os.path.abspath(__file__))
        audit_path = os.path.join(base_dir, "heartbeat_audit.jsonl")
        if os.path.exists(audit_path):
            os.remove(audit_path)
            print(f"✅ Local audit file removed: {audit_path}")

        print("\n🏆 RE-VALIDATION COMPLETE")
        print("The database now contains ONLY high-confidence, evidence-backed signals.")
        print("New pipeline (Database-First) is ready to populate the ledger.")

    except Exception as e:
        print(f"❌ Re-validation failed: {e}")

if __name__ == "__main__":
    asyncio.run(revalidate_system())
