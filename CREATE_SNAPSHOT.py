"""
Quantix AI Core - System Snapshot Creator
Creates a complete backup snapshot for disaster recovery
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path(__file__).parent
SNAPSHOT_DIR = BASE_DIR / "snapshots"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
SNAPSHOT_NAME = f"Quantix_Snapshot_{TIMESTAMP}"
SNAPSHOT_PATH = SNAPSHOT_DIR / SNAPSHOT_NAME

# Files and directories to include
INCLUDE_DIRS = [
    "backend/quantix_core",
    "backend/requirements.txt",
    "backend/runtime.txt",
]

INCLUDE_FILES = [
    ".env",
    "Procfile",
    "Dockerfile",
    "backend/quantix_core/engine/Rules.txt",
    "backend/quantix_core/engine/Quantix_AI Confidence.md",
]

INCLUDE_DOCS = [
    "*.md"
]

# Exclusions
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    ".venv",
    "venv",
    "node_modules",
    ".git",
    "*.log",
    "*.jsonl",
    "logs",
    "debug_*.py",
    "check_*.py",
    "test_*.py",
    "analyze_*.py",
    "audit_*.py",
]

def should_exclude(path: Path) -> bool:
    """Check if path should be excluded"""
    path_str = str(path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern.startswith("*."):
            if path_str.endswith(pattern[1:]):
                return True
        elif pattern in path_str:
            return True
    return False

def copy_with_exclusions(src: Path, dst: Path):
    """Copy directory with exclusions"""
    if not src.exists():
        print(f"⚠️  Skipping {src} (not found)")
        return
    
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"✓ Copied {src.name}")
    else:
        for item in src.rglob("*"):
            if should_exclude(item):
                continue
            
            rel_path = item.relative_to(src)
            dst_path = dst / rel_path
            
            if item.is_file():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dst_path)

def create_snapshot():
    """Create system snapshot"""
    print("=" * 80)
    print("  QUANTIX AI CORE - SYSTEM SNAPSHOT CREATOR")
    print("=" * 80)
    print()
    
    # Create snapshot directory
    print(f"[1/6] Creating snapshot directory: {SNAPSHOT_NAME}")
    SNAPSHOT_PATH.mkdir(parents=True, exist_ok=True)
    
    # Copy backend code
    print("\n[2/6] Copying backend code...")
    backend_src = BASE_DIR / "backend" / "quantix_core"
    backend_dst = SNAPSHOT_PATH / "backend" / "quantix_core"
    copy_with_exclusions(backend_src, backend_dst)
    
    # Copy configuration files
    print("\n[3/6] Copying configuration files...")
    for file_path in INCLUDE_FILES:
        src = BASE_DIR / file_path
        if src.exists():
            dst = SNAPSHOT_PATH / file_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"✓ Copied {src.name}")
        else:
            print(f"⚠️  Skipping {file_path} (not found)")
    
    # Copy requirements
    print("\n[4/6] Copying requirements...")
    req_src = BASE_DIR / "backend" / "requirements.txt"
    if req_src.exists():
        shutil.copy2(req_src, SNAPSHOT_PATH / "requirements.txt")
        print(f"✓ Copied requirements.txt")
    
    # Copy documentation
    print("\n[5/6] Copying documentation...")
    docs_dst = SNAPSHOT_PATH / "docs"
    docs_dst.mkdir(exist_ok=True)
    
    for md_file in BASE_DIR.glob("*.md"):
        shutil.copy2(md_file, docs_dst / md_file.name)
        print(f"✓ Copied {md_file.name}")
    
    # Create manifest
    print("\n[6/6] Creating snapshot manifest...")
    manifest = {
        "snapshot_name": SNAPSHOT_NAME,
        "created_at": datetime.now().isoformat(),
        "timestamp": TIMESTAMP,
        "contents": {
            "backend_code": "quantix_core engine and modules",
            "configuration": ".env, Procfile, Dockerfile",
            "documentation": "Rules.txt, Confidence.md, checkpoints",
            "requirements": "Python dependencies"
        },
        "restore_instructions": [
            "1. Stop all running services",
            "2. Backup current backend folder",
            "3. Copy snapshot backend to main directory",
            "4. Restore .env file",
            "5. Run: pip install -r requirements.txt",
            "6. Restart services"
        ]
    }
    
    manifest_path = SNAPSHOT_PATH / "SNAPSHOT_INFO.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Create README
    readme_path = SNAPSHOT_PATH / "README.txt"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write("QUANTIX AI CORE SNAPSHOT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Snapshot: {SNAPSHOT_NAME}\n\n")
        f.write("CONTENTS:\n")
        f.write("- Backend source code (quantix_core)\n")
        f.write("- Configuration files (.env, Procfile, etc)\n")
        f.write("- Documentation (Rules.txt, Confidence.md)\n")
        f.write("- Requirements and runtime specs\n\n")
        f.write("RESTORE:\n")
        f.write("See SNAPSHOT_INFO.json for detailed instructions\n")
    
    print()
    print("=" * 80)
    print("  SNAPSHOT CREATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"Location: {SNAPSHOT_PATH}")
    print(f"Size: {get_dir_size(SNAPSHOT_PATH):.2f} MB")
    print()
    print("To restore this snapshot:")
    print("  python restore_snapshot.py")
    print()

def get_dir_size(path: Path) -> float:
    """Get directory size in MB"""
    total = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return total / (1024 * 1024)

if __name__ == "__main__":
    try:
        create_snapshot()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
