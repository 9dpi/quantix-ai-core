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

# --- HELPER: DB LOGGING ---
def log_to_db(asset, status, direction="SYSTEM"):
    try:
        from quantix_core.database.connection import db
        from datetime import datetime, timezone
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": asset,
            "direction": direction,
            "status": str(status)[:200],
            "price": 0,
            "confidence": 0,
            "strength": 0
        }).execute()
    except:
        pass

# --- AUTO-RESTART LOOP ---
MAX_RESTARTS = 100
COOLDOWN_SEC = 15
cmd = [sys.executable, "-m", "quantix_core.engine.continuous_analyzer"]

for attempt in range(1, MAX_RESTARTS + 1):
    print(f"\n🔄 [Attempt {attempt}/{MAX_RESTARTS}] Starting Analyzer...")
    log_to_db("SYSTEM_ANALYZER", f"STARTING_ATTEMPT_{attempt}", "LAUNCHER")
    
    try:
        process = subprocess.Popen(
            cmd, 
            env=os.environ.copy(), 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            bufsize=1
        )
        
        import threading
        def log_stream(stream):
            for line in iter(stream.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    print(f"[ANALYZER] {clean_line}")
                    log_to_db("ANALYZER_LOG", clean_line[:200], "STDOUT")
                    
        t = threading.Thread(target=log_stream, args=(process.stdout,), daemon=True)
        t.start()
        
        exit_code = process.wait()
        print(f"⚠️ Analyzer exited with code {exit_code}")
        log_to_db("SYSTEM_ANALYZER", f"EXITED_CODE_{exit_code}", "LAUNCHER")
        
    except KeyboardInterrupt:
        print("🛑 Analyzer stopped by user (Ctrl+C)")
        break
    except Exception as e:
        print(f"❌ Analyzer error: {e}")
        log_to_db("SYSTEM_ANALYZER", f"ERROR_{str(e)[:50]}", "LAUNCHER")
    
    if attempt < MAX_RESTARTS:
        print(f"⏳ Restarting in {COOLDOWN_SEC}s...")
        time.sleep(COOLDOWN_SEC)

print("🛑 Analyzer max restarts reached. Exiting launcher.")
