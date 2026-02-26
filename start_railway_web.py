import os
import sys
import subprocess

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
    from datetime import datetime, timezone
    db.client.table("fx_analysis_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": "SYSTEM_WEB",
        "direction": "STARTUP",
        "status": f"LAUNCHING_PORT_{port}",
        "price": 0,
        "confidence": 1.0,
        "strength": 1.0
    }).execute()
    print("✅ Web Startup proof logged to DB")
except Exception as e:
    print(f"❌ Failed to log web startup proof: {e}")

cmd = [sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", "--host", "0.0.0.0", "--port", port, "--proxy-headers"]
# Explicitly pass the environment
subprocess.run(cmd, env=os.environ.copy())

