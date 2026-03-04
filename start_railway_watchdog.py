import os
import sys
import subprocess
import time

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Watchdog Launcher (Auto-Restart) ---")
print(f"CWD: {os.getcwd()}")

# --- AUTO-RESTART LOOP ---
MAX_RESTARTS = 50
COOLDOWN_SEC = 15
cmd = [sys.executable, "-m", "quantix_core.engine.watchdog"]

for attempt in range(1, MAX_RESTARTS + 1):
    print(f"\n[Attempt {attempt}/{MAX_RESTARTS}] Starting Watchdog...")
    try:
        result = subprocess.run(cmd, env=os.environ.copy())
        exit_code = result.returncode
        print(f"Watchdog exited with code {exit_code}")
    except KeyboardInterrupt:
        print("Watchdog stopped by user (Ctrl+C)")
        break
    except Exception as e:
        print(f"Watchdog crashed: {e}")
    
    if attempt < MAX_RESTARTS:
        print(f"Restarting in {COOLDOWN_SEC}s...")
        try:
            from quantix_core.database.connection import db
            from datetime import datetime, timezone
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "SYSTEM_WATCHDOG",
                "direction": "SYSTEM",
                "status": f"AUTO_RESTART_ATTEMPT_{attempt}",
                "price": 0,
                "confidence": 0.0,
                "strength": 0.0
            }).execute()
        except:
            pass
        time.sleep(COOLDOWN_SEC)

print("Watchdog max restarts reached. Exiting launcher.")
