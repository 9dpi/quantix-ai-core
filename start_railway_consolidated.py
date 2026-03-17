import os
import sys
import subprocess
import threading
import time
from datetime import datetime, timezone

# Add backend to path
project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

print(f"--- Quantix CONSOLIDATED Launcher (v4.1.3) ---")
print(f"Time: {datetime.now(timezone.utc).isoformat()}")
print(f"CWD: {project_root}")

# Port detection (for Web API)
port = os.environ.get("PORT", "8080")

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

def run_service(name, cmd, asset_name, log_asset, direction="STDOUT", cwd=None, silence_timeout=900):
    """Run a service with an auto-restart loop and DB logging"""
    if cwd is None:
        cwd = project_root
        
    print(f"🚀 [Launcher] Starting {name} (Watchdog: {silence_timeout}s)...")
    attempt = 0
    
    while True:
        attempt += 1
        log_to_db(asset_name, f"STARTING_ATTEMPT_{attempt}", "LAUNCHER")
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Use a non-blocking approach to monitor output and detect hangs
            last_output_at = time.time()
            
            # We use a separate thread or a polling loop to read lines
            def monitor_output():
                nonlocal last_output_at
                for line in iter(process.stdout.readline, ''):
                    clean_line = line.strip()
                    if clean_line:
                        last_output_at = time.time()
                        print(f"[{name}] {clean_line}")
                        
                        # v4.7.2: Log ALL lines to DB during the first 1 minute of a process for visibility
                        # This avoids silent failures. After that, we filter again.
                        is_startup = (time.time() - proc_start_at < 60)
                        
                        upper_line = clean_line.upper()
                        is_error = any(kw in upper_line for kw in ["ERROR", "CRITICAL", "EXCEPTION", "[BOOT]", "FOUND", "FAILED"])
                        is_success = any(kw in upper_line for kw in ["SUCCESS", "🚀", "🎯", "SIGNAL", "LOCKED"])
                        
                        if is_startup or is_error or is_success:
                            def _safe_log(_line):
                                try:
                                    log_direction = "UVICORN_LOG" if name == "WEB" else "STDOUT"
                                    log_to_db(log_asset, _line[:200], log_direction)
                                except: pass
                            threading.Thread(target=_safe_log, args=(clean_line,), daemon=True).start()
            
            proc_start_at = time.time()
            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()
            
            # Main monitoring loop: Wait for process or timeout
            while process.poll() is None:
                if time.time() - last_output_at > silence_timeout:
                    print(f"🚨 [Launcher] {name} HUNG (silent for {silence_timeout}s). Killing...")
                    process.kill() # Trigger kill BEFORE doing risky network operations
                    threading.Thread(target=lambda: log_to_db(asset_name, f"KILLED_BY_WATCHDOG_SILENCE", "LAUNCHER"), daemon=True).start()
                    break
                time.sleep(10)
            
            process.wait()
            log_to_db(asset_name, f"EXITED_CODE_{process.returncode}", "LAUNCHER")
            print(f"⚠️ [Launcher] {name} exited with code {process.returncode}. Restarting in 10s...")
        except Exception as e:
            log_to_db(asset_name, f"ERROR_{str(e)[:50]}", "LAUNCHER")
            print(f"❌ [Launcher] {name} failed: {e}. Restarting in 10s...")
        
        time.sleep(10)

# 1. WEB API (Must run on the specific $PORT)
web_cmd = [
    sys.executable, "-u", "-m", "uvicorn", "quantix_core.api.main:app",
    "--host", "0.0.0.0",
    "--port", port,
    "--proxy-headers"
]

# 2. ANALYZER
analyzer_cmd = [sys.executable, "-u", "-m", "quantix_core.engine.continuous_analyzer"]

# 3. VALIDATOR
validator_script = os.path.join(backend_path, "run_pepperstone_validator.py")
validator_cmd = [sys.executable, "-u", validator_script]

if __name__ == "__main__":
    # Create threads for each service with appropriate Audit Asset names
    # WEB: 1 hour silence timeout (3600s) because uvicorn is silent when no requests
    threads = [
        threading.Thread(target=run_service, args=("WEB", web_cmd, "SYSTEM_WEB", "UVICORN_LOG"), kwargs={"silence_timeout": 3600}, daemon=True),
        threading.Thread(target=run_service, args=("ANALYZER", analyzer_cmd, "SYSTEM_ANALYZER", "ANALYZER_LOG"), kwargs={"silence_timeout": 900}, daemon=True),
        threading.Thread(target=run_service, args=("VALIDATOR", validator_cmd, "VALIDATOR", "VALIDATOR_LOG"), kwargs={"silence_timeout": 600}, daemon=True)
    ]
    
    for t in threads:
        t.start()
        time.sleep(2) # Stagger start times
        
    print("✨ All services are launched in parallel. Monitoring...")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("🛑 Shutdown requested.")
