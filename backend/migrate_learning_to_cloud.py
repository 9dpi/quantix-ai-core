
import json
import os
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

def migrate_to_cloud():
    print("🚀 MIGRATING LOCAL LEARNING DATA TO SUPABASE...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_file = os.path.join(base_dir, 'backend', 'heartbeat_audit.jsonl')
    
    if not os.path.exists(audit_file):
        print("❌ Local audit file not found.")
        return

    history = []
    with open(audit_file, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get("status") == "ANALYZED":
                        history.append(data)
                except:
                    continue
    
    if not history:
        print("ℹ️ No local data to migrate.")
        return

    print(f"📦 Found {len(history)} samples. Checking Supabase...")
    
    try:
        # 1. Check if table exists by trying a select
        db.client.table(settings.TABLE_ANALYSIS_LOG).select("id").limit(1).execute()
    except Exception as e:
        print(f"⚠️ Table {settings.TABLE_ANALYSIS_LOG} might not exist. Please ensure it is created in Supabase.")
        print(f"Error detail: {e}")
        return

    # 2. Push in batches of 50
    batch_size = 50
    success_count = 0
    for i in range(0, len(history), batch_size):
        batch = history[i:i+batch_size]
        try:
            db.client.table(settings.TABLE_ANALYSIS_LOG).insert(batch).execute()
            success_count += len(batch)
            print(f"✅ Migrated {success_count}/{len(history)}...")
        except Exception as e:
            print(f"❌ Batch insertion failed: {e}")
            break

    print(f"🏁 Migration complete. {success_count} samples pushed to cloud.")

if __name__ == "__main__":
    migrate_to_cloud()
