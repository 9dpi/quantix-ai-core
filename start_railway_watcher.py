import os
import sys
import subprocess
import time

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Watcher Launcher (Auto-Restart) ---")
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

# --- AUTO-RESTART LOOP ---
MAX_RESTARTS = 50
COOLDOWN_SEC = 10
script_path = os.path.join(backend_path, "run_signal_watcher.py")
cmd = [sys.executable, script_path]

for attempt in range(1, MAX_RESTARTS + 1):
    print(f"\n🔄 [Attempt {attempt}/{MAX_RESTARTS}] Starting Watcher...")
    try:
        # Capture stderr to debug crash-at-launch
        result = subprocess.run(cmd, env=os.environ.copy(), capture_output=True, text=True)
        exit_code = result.returncode
        
        if exit_code != 0:
            print(f"⚠️ Watcher exited with code {exit_code}")
            print(f"❌ Stderr: {result.stderr}")
            error_reason = f"Exit {exit_code}: {result.stderr[:100]}"
        else:
            print(f"✅ Watcher exited normally (code 0)")
            error_reason = "Normal Exit"
            
    except Exception as e:
        print(f"❌ Launcher crash: {e}")
        error_reason = str(e)
    
    if attempt < MAX_RESTARTS:
        print(f"⏳ Restarting in {COOLDOWN_SEC}s...")
        try:
            # Log restart event with REASON to DB
            from quantix_core.database.connection import db
            from datetime import datetime, timezone
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "SYSTEM_WATCHER",
                "direction": "SYSTEM",
                "status": f"AUTO_RESTART_{attempt}",
                "message": f"Reason: {error_reason[:150]}",
                "price": 0,
                "confidence": 0.0,
                "strength": 0.0
            }).execute()
        except:
            pass
        time.sleep(COOLDOWN_SEC)

print("🛑 Watcher max restarts reached. Exiting launcher.")
