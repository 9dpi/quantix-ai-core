import os
import sys
import subprocess
import time
from datetime import datetime, timezone

print(f"--- Quantix Launcher Starting ---")
print(f"Time: {datetime.now(timezone.utc).isoformat()}")
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Add backend to path
project_root = os.getcwd()
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)
os.environ["PYTHONPATH"] = backend_path

# Port detection
port = os.environ.get("PORT", "8080")
print(f"Target Port: {port}")

import threading

def log_to_db(direction, status, explain=None):
    """Log launcher events to Supabase for audit compatibility (Non-blocking)"""
    def _task():
        try:
            from quantix_core.database.connection import db
            payload = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "asset": "SYSTEM_WEB",
                "direction": direction,
                "status": f"{status} | {explain}" if explain else status,
                "price": 0, "confidence": 1.0, "strength": 1.0
            }
            db.client.table("fx_analysis_log").insert(payload).execute()
        except Exception as e:
            pass
    threading.Thread(target=_task, daemon=True).start()

log_to_db("LAUNCHER", f"Started on port {port}")

# Test Import
print("🔍 Importing app...")
try:
    from quantix_core.api.main import app
    print("✅ App imported")
    log_to_db("LAUNCHER", "Import OK")
except Exception as e:
    import traceback
    tb = traceback.format_exc()
    print(f"❌ Import failed: {e}")
    log_to_db("CRASH", f"IMPORT_FAIL: {e}", tb)
    sys.exit(1)

# Final command
cmd = [
    sys.executable, "-m", "uvicorn", "quantix_core.api.main:app", 
    "--host", "0.0.0.0", 
    "--port", port, 
    "--proxy-headers",
    "--forwarded-allow-ips", "*"
]

print(f"🚀 Launching Uvicorn: {' '.join(cmd)}")
log_to_db("LAUNCHER", "STARTING_UVICORN", f"Port: {port}")

sys.stdout.flush()
sys.stderr.flush()

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
            print(f"[UVICORN] {clean_line}")
            log_to_db("UVICORN_LOG", clean_line[:200])
            
t = threading.Thread(target=log_stream, args=(process.stdout,), daemon=True)
t.start()

# NEW: Self-Ping diagnostic
def self_ping():
    time.sleep(10) # wait for uvicorn to boot
    import urllib.request
    ping_url = f"http://127.0.0.1:{port}/api/v1/health"
    try:
        req = urllib.request.Request(ping_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            body = response.read().decode('utf-8')[:100]
            log_to_db("SELF_PING", f"SUCCESS | HTTP {status} | Body: {body}")
    except Exception as e:
        log_to_db("SELF_PING", f"FAILED | {e}")
        
pinger = threading.Thread(target=self_ping, daemon=True)
pinger.start()

exit_code = process.wait()

if exit_code != 0:
    print(f"❌ Uvicorn Crashed with code {exit_code}")
    log_to_db("CRASH", f"UVICORN_EXIT_{exit_code}")
    sys.exit(1)
