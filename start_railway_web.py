import os
import sys
import subprocess
from datetime import datetime, timezone

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

# Port detection logic
# Priority: 1. PORT (Railway default), 2. API_PORT (User custom), 3. Default 8080
port = os.environ.get("PORT")
if not port:
    port = os.environ.get("API_PORT", "8080")

print(f"--- Quantix Launcher ---")
print(f"Starting uvicorn on port {port}...")

# --- STARTUP DIAGNOSTIC ---
try:
    from quantix_core.database.connection import db
    
    # Test Import
    try:
        from quantix_core.api.main import app
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "SYSTEM_WEB",
            "direction": "STARTUP",
            "status": f"Ready on port {port}",
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
            "explainability": tb[:1000]
        }).execute()
        sys.exit(1)

except Exception as e:
    print(f"❌ Diagnostic failed: {e}")

# --- START UVICORN ---
# Using --proxy-headers and --forwarded-allow-ips='*' for Railway Edge
cmd = [
    sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", 
    "--host", "0.0.0.0", 
    "--port", port, 
    "--proxy-headers",
    "--forwarded-allow-ips", "*"
]
subprocess.run(cmd, env=os.environ.copy())
