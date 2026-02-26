import os
import sys
import subprocess
import time
from datetime import datetime, timezone

print(f"--- Quantix Launcher Starting ---")
print(f"Time: {datetime.now(timezone.utc).isoformat()}")
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

# Port detection
port = os.environ.get("PORT", "8080")
print(f"Target Port: {port}")

try:
    from quantix_core.database.connection import db
    
    def log_to_db(direction, status, explain=None):
        try:
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "SYSTEM_WEB",
                "direction": direction,
                "status": status,
                "explainability": explain,
                "price": 0, "confidence": 1.0, "strength": 1.0
            }).execute()
        except Exception as e:
            print(f"DB Log Failed: {e}")

    log_to_db("LAUNCHER", f"Started on port {port}")

    # Test Import
    print("🔍 Importing app...")
    try:
        from quantix_core.api.main import app
        print("✅ App imported")
        log_to_db("LAUNCHER", "Import OK")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"❌ Import failed: {e}")
        log_to_db("CRASH", f"IMPORT_FAIL: {e}", tb)
        sys.exit(1)

    # Final command
    cmd = [
        sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", port, 
        "--proxy-headers",
        "--forwarded-allow-ips", "*"
    ]
    
    print(f"🚀 Executing: {' '.join(cmd)}")
    # We use Popen so we can potentially monitor it, but for now just wait
    # Actually, subprocess.run is safer to ensure it keeps running
    subprocess.run(cmd, env=os.environ.copy())

except Exception as e:
    print(f"❌ Fatal Launcher Error: {e}")
    try:
        from quantix_core.database.connection import db
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "SYSTEM_WEB",
            "direction": "CRASH",
            "status": f"FATAL: {e}"
        }).execute()
    except: pass
