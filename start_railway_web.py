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

print(f"--- Quantix CONSOLIDATED Launcher (v4.7.2 STABLE) ---")
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

def run_service(name, cmd, asset_name, log_asset, direction="STDOUT", cwd=None):
    """Run a service with an auto-restart loop and DB logging"""
    if cwd is None:
        cwd = project_root
        
    print(f"🚀 [Launcher] Starting {name}...")
    attempt = 0
    
    # Silence Watchdog: Kill process if no output for 15 minutes
    SILENCE_TIMEOUT = 900 # 15 minutes
    
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
            
            last_output_at = time.time()
            proc_start_at = time.time()
            
            def monitor_output():
                nonlocal last_output_at
                for line in iter(process.stdout.readline, ''):
                    clean_line = line.strip()
                    if clean_line:
                        last_output_at = time.time()
                        print(f"[{name}] {clean_line}")
                        
                        # v4.7.2: Log ALL lines to DB during the first 1 minute for visibility
                        is_startup = (time.time() - proc_start_at < 60)
                        upper_line = clean_line.upper()
                        is_error = "ERROR" in upper_line or "CRITICAL" in upper_line or "EXCEPTION" in upper_line or "[BOOT]" in upper_line
                        
                        if is_startup or is_error:
                            def _safe_log(_line):
                                try:
                                    log_direction = "UVICORN_LOG" if name == "WEB" else "STDOUT"
                                    log_to_db(log_asset, _line[:200], log_direction)
                                except: pass
                            threading.Thread(target=_safe_log, args=(clean_line,), daemon=True).start()
            
            monitor_thread = threading.Thread(target=monitor_output, daemon=True)
            monitor_thread.start()
            
            while process.poll() is None:
                if time.time() - last_output_at > SILENCE_TIMEOUT:
                    print(f"🚨 [Launcher] {name} HUNG (silent for {SILENCE_TIMEOUT}s). Killing...")
                    process.kill()
                    break
                time.sleep(10)
            
            process.wait()
            log_to_db(asset_name, f"EXITED_CODE_{process.returncode}", "LAUNCHER")
            print(f"⚠️ [Launcher] {name} exited with code {process.returncode}. Restarting in 10s...")
        except Exception as e:
            msg = str(e)[:100]
            log_to_db(asset_name, f"ERROR_{msg}", "LAUNCHER")
            print(f"❌ [Launcher] {name} failed: {e}. Restarting in 10s...")
        
        # v4.7.2: If this is the WEB service and it failed to bind, just wait longer before restart
        # but keep the launcher ALIVE for background tasks (Analyzer) to work.
        time.sleep(30)

# 1. WEB API
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
    # v4.7.2: Final consolidation for Railway Web Service
    threads = [
        threading.Thread(target=run_service, args=("WEB", web_cmd, "SYSTEM_WEB", "UVICORN_LOG"), daemon=True),
        threading.Thread(target=run_service, args=("ANALYZER", analyzer_cmd, "SYSTEM_ANALYZER", "ANALYZER_LOG"), daemon=True),
        threading.Thread(target=run_service, args=("VALIDATOR", validator_cmd, "VALIDATOR", "VALIDATOR_LOG"), daemon=True)
    ]
    
    for t in threads:
        t.start()
        time.sleep(2)
        
    print("✨ All services launched. Monitoring...")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("🛑 Shutdown requested.")
