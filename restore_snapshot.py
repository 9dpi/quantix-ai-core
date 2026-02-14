"""
Quantix AI Core - Snapshot Restore Utility
Restores a previous snapshot with safety backups
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
SNAPSHOT_DIR = BASE_DIR / "snapshots"

def list_snapshots():
    """List available snapshots"""
    if not SNAPSHOT_DIR.exists():
        return []
    
    snapshots = []
    for item in SNAPSHOT_DIR.iterdir():
        if item.is_dir() and item.name.startswith("Quantix_Snapshot_"):
            info_file = item / "SNAPSHOT_INFO.json"
            if info_file.exists():
                with open(info_file, 'r') as f:
                    info = json.load(f)
                snapshots.append({
                    "name": item.name,
                    "path": item,
                    "created_at": info.get("created_at", "Unknown"),
                    "size": get_dir_size(item)
                })
    
    return sorted(snapshots, key=lambda x: x["created_at"], reverse=True)

def get_dir_size(path: Path) -> float:
    """Get directory size in MB"""
    total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return total / (1024 * 1024)

def create_backup():
    """Create backup of current system"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backend_backup_{timestamp}"
    backup_path = BASE_DIR / backup_name
    
    print(f"Creating backup: {backup_name}")
    
    backend_src = BASE_DIR / "backend"
    if backend_src.exists():
        shutil.copytree(backend_src, backup_path / "backend", 
                       ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.venv', 'venv'))
        print(f"✓ Backup created: {backup_path}")
        return backup_path
    else:
        print("⚠️  No backend directory to backup")
        return None

def restore_snapshot(snapshot_path: Path):
    """Restore a snapshot"""
    print()
    print("=" * 80)
    print("  QUANTIX AI CORE - SNAPSHOT RESTORE")
    print("=" * 80)
    print()
    
    # Load snapshot info
    info_file = snapshot_path / "SNAPSHOT_INFO.json"
    if info_file.exists():
        with open(info_file, 'r') as f:
            info = json.load(f)
        print(f"Snapshot: {info['snapshot_name']}")
        print(f"Created: {info['created_at']}")
        print()
    
    # Confirm
    print("WARNING: This will overwrite current files!")
    print()
    confirm = input("Type 'YES' to confirm restore: ")
    
    if confirm != "YES":
        print("\nRestore cancelled.")
        return
    
    print()
    print("[1/4] Creating backup of current system...")
    backup_path = create_backup()
    
    print("\n[2/4] Restoring backend code...")
    backend_src = snapshot_path / "backend"
    backend_dst = BASE_DIR / "backend"
    
    if backend_src.exists():
        # Remove old backend (except .venv)
        if backend_dst.exists():
            for item in backend_dst.iterdir():
                if item.name != ".venv":
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        
        # Copy snapshot backend
        shutil.copytree(backend_src, backend_dst, dirs_exist_ok=True)
        print("✓ Backend code restored")
    else:
        print("⚠️  No backend in snapshot")
    
    print("\n[3/4] Restoring configuration files...")
    config_files = [".env", "Procfile", "Dockerfile"]
    for file_name in config_files:
        src = snapshot_path / file_name
        if src.exists():
            shutil.copy2(src, BASE_DIR / file_name)
            print(f"✓ Restored {file_name}")
    
    print("\n[4/4] Verifying restore...")
    core_file = BASE_DIR / "backend" / "quantix_core" / "engine" / "continuous_analyzer.py"
    if core_file.exists():
        print("✓ Core files verified")
    else:
        print("✗ ERROR: Core files missing!")
        print(f"Backup available at: {backup_path}")
        return
    
    print()
    print("=" * 80)
    print("  RESTORE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"Snapshot restored: {snapshot_path.name}")
    if backup_path:
        print(f"Backup saved to: {backup_path}")
    print()
    print("NEXT STEPS:")
    print("1. Review restored files")
    print("2. Check .env configuration")
    print("3. Run: pip install -r requirements.txt (if needed)")
    print("4. Restart services")
    print()

def main():
    """Main restore interface"""
    print("=" * 80)
    print("  QUANTIX AI CORE - SNAPSHOT RESTORE UTILITY")
    print("=" * 80)
    print()
    
    snapshots = list_snapshots()
    
    if not snapshots:
        print("No snapshots found!")
        print(f"Create a snapshot first using: python create_snapshot.py")
        return
    
    print("Available snapshots:")
    print()
    for i, snap in enumerate(snapshots, 1):
        print(f"{i}. {snap['name']}")
        print(f"   Created: {snap['created_at']}")
        print(f"   Size: {snap['size']:.2f} MB")
        print()
    
    try:
        choice = int(input("Select snapshot number (or 0 to cancel): "))
        if choice == 0:
            print("Cancelled.")
            return
        
        if 1 <= choice <= len(snapshots):
            selected = snapshots[choice - 1]
            restore_snapshot(selected['path'])
        else:
            print("Invalid selection.")
    except ValueError:
        print("Invalid input.")
    except KeyboardInterrupt:
        print("\nCancelled.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
