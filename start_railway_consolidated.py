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
    """Log launcher events to Supabase for audit compatibility"""
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

def run_service(name, cmd, asset_name, log_asset, direction="STDOUT", cwd=None):
    """Run a service with an auto-restart loop and DB logging"""
    if cwd is None:
        cwd = project_root
        
    print(f"🚀 [Launcher] Starting {name}...")
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
            
            # Stream output with prefix and DB logging
            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    print(f"[{name}] {clean_line}")
                    # Map direction for Web specifically per internal_health_check.py
                    log_direction = "UVICORN_LOG" if name == "WEB" else "STDOUT"
                    log_to_db(log_asset, clean_line[:200], log_direction)
            
            process.wait()
            log_to_db(asset_name, f"EXITED_CODE_{process.returncode}", "LAUNCHER")
            print(f"⚠️ [Launcher] {name} exited with code {process.returncode}. Restarting in 10s...")
        except Exception as e:
            log_to_db(asset_name, f"ERROR_{str(e)[:50]}", "LAUNCHER")
            print(f"❌ [Launcher] {name} failed: {e}. Restarting in 10s...")
        
        time.sleep(10)

# 1. WEB API (Must run on the specific $PORT)
web_cmd = [
    sys.executable, "-m", "uvicorn", "quantix_core.api.main:app",
    "--host", "0.0.0.0",
    "--port", port,
    "--proxy-headers",
    "--forwarded-allow-ips", "*"
]

# 2. ANALYZER
analyzer_cmd = [sys.executable, "-m", "quantix_core.engine.continuous_analyzer"]

# 3. VALIDATOR
validator_script = os.path.join(backend_path, "run_pepperstone_validator.py")
validator_cmd = [sys.executable, validator_script]

if __name__ == "__main__":
    # Create threads for each service with appropriate Audit Asset names
    threads = [
        threading.Thread(target=run_service, args=("WEB", web_cmd, "SYSTEM_WEB", "UVICORN_LOG"), daemon=True),
        threading.Thread(target=run_service, args=("ANALYZER", analyzer_cmd, "SYSTEM_ANALYZER", "ANALYZER_LOG"), daemon=True),
        threading.Thread(target=run_service, args=("VALIDATOR", validator_cmd, "VALIDATOR", "VALIDATOR_LOG"), daemon=True)
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
