import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Watcher Launcher ---")
print(f"CWD: {os.getcwd()}")

# --- STARTUP PROOF ---
try:
    from quantix_core.database.connection import db
    from datetime import datetime, timezone
    db.client.table("fx_analysis_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": "SYSTEM_WATCHER",
        "direction": "STARTUP",
        "status": "LAUNCHING",
        "price": 0,
        "confidence": 1.0,
        "strength": 1.0
    }).execute()
    print("✅ Startup proof logged to DB")
except Exception as e:
    print(f"❌ Failed to log startup proof: {e}")

# Watcher is a script in backend folder
script_path = os.path.join(backend_path, "run_signal_watcher.py")
cmd = [sys.executable, script_path]
subprocess.run(cmd, env=os.environ.copy())
