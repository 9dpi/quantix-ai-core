import os
import sys
import subprocess

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Validator Launcher ---")
print(f"CWD: {os.getcwd()}")

try:
    from quantix_core.database.connection import db
    from datetime import datetime, timezone

    def log_crash(msg):
        try:
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "VALIDATOR",
                "status": "CRASH_REPORT",
                "direction": "ERROR",
                "price": 0,
                "confidence": 0,
                "strength": 0,
                "disclaimer": msg[:200]
            }).execute()
        except:
            pass

    # Validator is a script in backend folder
    script_path = os.path.join(backend_path, "run_pepperstone_validator.py")
    cmd = [sys.executable, script_path]
    print(f"Starting validator: {cmd}")
    
    # Use Popen to allow better control if needed, but run is fine for basic
    result = subprocess.run(cmd, env=os.environ.copy())
    
    if result.returncode != 0:
        log_crash(f"Validator exited with code {result.returncode}")

except Exception as e:
    print(f"Launcher level crash: {e}")
    try:
        log_crash(f"Launcher crash: {e}")
    except:
        pass
    sys.exit(1)
