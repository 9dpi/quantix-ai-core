import os
import sys
import subprocess
import threading
import time
from datetime import datetime, timezone

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix Watcher Launcher (Auto-Restart) ---")
print(f"CWD: {os.getcwd()}")

# --- HELPER: DB LOGGING ---
def log_to_db(asset, status, direction="SYSTEM"):
    """Log launcher events to Supabase for audit compatibility (Non-blocking)"""
    def _task():
        try:
            from quantix_core.database.connection import db
            db.client.table("fx_analysis_log").insert({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": asset,
                "direction": direction,
                "status": str(status)[:200],
                "price": 0, "confidence": 0, "strength": 0
            }).execute()
        except:
            pass
    threading.Thread(target=_task, daemon=True).start()

# --- STARTUP PROOF ---
log_to_db("SYSTEM_WATCHER", "LAUNCHING", "STARTUP")

# --- AUTO-RESTART LOOP ---
MAX_RESTARTS = 100
COOLDOWN_SEC = 15
script_path = os.path.join(backend_path, "run_signal_watcher.py")
cmd = [sys.executable, script_path]

for attempt in range(1, MAX_RESTARTS + 1):
    print(f"\n🔄 [Attempt {attempt}/{MAX_RESTARTS}] Starting Watcher...")
    log_to_db("SYSTEM_WATCHER", f"STARTING_ATTEMPT_{attempt}", "LAUNCHER")
    
    try:
        process = subprocess.Popen(
            cmd, 
            env=os.environ.copy(), 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )
        
        def log_stream(stream):
            for line in iter(stream.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    print(f"[WATCHER] {clean_line}")
                    log_to_db("WATCHER_LOG", clean_line[:200], "STDOUT")
                    
        t = threading.Thread(target=log_stream, args=(process.stdout,), daemon=True)
        t.start()
        
        exit_code = process.wait()
        print(f"⚠️ Watcher exited with code {exit_code}")
        log_to_db("SYSTEM_WATCHER", f"EXITED_CODE_{exit_code}", "LAUNCHER")
        
    except KeyboardInterrupt:
        print("🛑 Watcher stopped by user (Ctrl+C)")
        break
    except Exception as e:
        print(f"❌ Watcher error: {e}")
        log_to_db("SYSTEM_WATCHER", f"ERROR_{str(e)[:50]}", "LAUNCHER")
    
    if attempt < MAX_RESTARTS:
        print(f"⏳ Restarting in {COOLDOWN_SEC}s...")
        time.sleep(COOLDOWN_SEC)
