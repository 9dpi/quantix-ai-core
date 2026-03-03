import os
import sys
import subprocess
import time

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Analyzer Launcher (Auto-Restart) ---")
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ['PYTHONPATH']}")

# --- STARTUP PROOF ---
try:
    from quantix_core.database.connection import db
    from datetime import datetime, timezone
    db.client.table("fx_analysis_log").insert({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset": "SYSTEM_ANALYZER",
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
cmd = [sys.executable, "-m", "quantix_core.engine.continuous_analyzer"]

for attempt in range(1, MAX_RESTARTS + 1):
    print(f"\n🔄 [Attempt {attempt}/{MAX_RESTARTS}] Starting Analyzer...")
    try:
        result = subprocess.run(cmd, env=os.environ.copy())
        exit_code = result.returncode
        print(f"⚠️ Analyzer exited with code {exit_code}")
    except KeyboardInterrupt:
        print("🛑 Analyzer stopped by user (Ctrl+C)")
        break
    except Exception as e:
        print(f"❌ Analyzer crashed: {e}")
    
    if attempt < MAX_RESTARTS:
        print(f"⏳ Restarting in {COOLDOWN_SEC}s...")
        try:
            from quantix_core.database.connection import db
            from datetime import datetime, timezone
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "SYSTEM_ANALYZER",
                "direction": "SYSTEM",
                "status": f"AUTO_RESTART_ATTEMPT_{attempt}",
                "price": 0,
                "confidence": 0.0,
                "strength": 0.0
            }).execute()
        except:
            pass
        time.sleep(COOLDOWN_SEC)

print("🛑 Analyzer max restarts reached. Exiting launcher.")
