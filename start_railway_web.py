import os
import sys
import subprocess
from datetime import datetime, timezone

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

port = os.environ.get("PORT", "8080")
print(f"--- Quantix Launcher ---")
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")
print(f"Starting uvicorn on port {port}...")

# --- STARTUP DIAGNOSTIC ---
try:
    from quantix_core.database.connection import db
    
    # 1. Log Env keys
    env_keys = ", ".join(sorted(os.environ.keys()))
    db.client.table("fx_analysis_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": "SYSTEM_WEB",
        "direction": "ENV_DEBUG",
        "status": f"PORT={port} | KEYS: {env_keys[:150]}",
        "price": 0, "confidence": 1.0, "strength": 1.0
    }).execute()

    # 2. Test Import
    try:
        print("🔍 Testing app import...")
        from quantix_core.api.main import app
        print("✅ App imported successfully in launcher")
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "SYSTEM_WEB",
            "direction": "IMPORT_OK",
            "status": "Ready for uvicorn",
            "price": 0, "confidence": 1.0, "strength": 1.0
        }).execute()
    except Exception as import_err:
        import traceback
        tb = traceback.format_exc()
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "SYSTEM_WEB",
            "direction": "CRASH",
            "status": f"IMPORT_FAIL: {str(import_err)}",
            "explainability": tb[:1000],
            "price": 0, "confidence": 0, "strength": 0
        }).execute()
        print(f"❌ App import failed: {import_err}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Diagnostic failed: {e}")

# --- START UVICORN ---
cmd = [sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", "--host", "0.0.0.0", "--port", port, "--proxy-headers"]
subprocess.run(cmd, env=os.environ.copy())
