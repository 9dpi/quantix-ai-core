
import os
import shutil
import json
from datetime import datetime
import zipfile

def create_full_snapshot():
    # 1. Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"Quantix_Full_Snapshot_{timestamp}"
    snapshot_dir = os.path.join(base_dir, "snapshots", snapshot_name)
    zip_path = os.path.join(base_dir, "snapshots", f"{snapshot_name}.zip")
    
    print(f"🚀 INITIALIZING FULL SYSTEM SNAPSHOT: {snapshot_name}")
    
    if not os.path.exists(os.path.join(base_dir, "snapshots")):
        os.makedirs(os.path.join(base_dir, "snapshots"))

    # 2. Define payload
    # We back up: code, configs, local data, and dashboard state
    items_to_backup = [
        "backend/.env",
        "backend/heartbeat_audit.jsonl",
        "backend/quantix_core",
        "backend/analyze_heartbeat.py",
        "dashboard/learning_data.json",
        "dashboard/index.html",
        "static",
        "START_QUANTIX.bat",
        "PORTABILITY_GUIDE.md"
    ]

    try:
        if os.path.exists(snapshot_dir):
            shutil.rmtree(snapshot_dir)
        os.makedirs(snapshot_dir)

        # 3. Copy files
        for item in items_to_backup:
            src = os.path.join(base_dir, item)
            dst = os.path.join(snapshot_dir, item)
            
            if os.path.exists(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
                print(f"✅ Backed up: {item}")
            else:
                print(f"⚠️ Item not found, skipping: {item}")

        # 4. Create Metadata
        metadata = {
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "type": "FULL_RESTORE_POINT",
            "files": items_to_backup
        }
        with open(os.path.join(snapshot_dir, "snapshot_metadata.json"), "w") as f:
            json.dump(metadata, f, indent=4)

        # 5. Compress to ZIP
        print(f"📦 Compressing to {zip_path}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(snapshot_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(snapshot_dir))
                    zipf.write(file_path, arcname)

        # Optional: Cleanup directory after zip
        # shutil.rmtree(snapshot_dir)
        
        print(f"\n✨ SNAPSHOT COMPLETE! ✨")
        print(f"Location: {zip_path}")
        print(f"This file contains everything needed to restore Quantix on any machine.")

    except Exception as e:
        print(f"❌ Snapshot failed: {e}")

if __name__ == "__main__":
    create_full_snapshot()
