import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
sys.path.append(backend_path)

from quantix_core.database.connection import db

def log_error(msg):
    try:
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "SYSTEM_WATCHER",
            "status": "CRASH_REPORT",
            "direction": "ERROR",
            "price": 0,
            "confidence": 0,
            "strength": 0,
            "disclaimer": msg[:200]
        }).execute()
    except:
        pass
    print(msg)

try:
    print("Pre-flight check for Watcher...")
    import twelvedata
    print("✅ twelvedata imported")
    from quantix_core.config.settings import settings
    print(f"✅ Settings loaded (Instance: {settings.INSTANCE_NAME})")
    from quantix_core.engine.signal_watcher import SignalWatcher
    print("✅ SignalWatcher class imported")
    
    # Check dependencies
    import requests
    import supabase
    import loguru
    print("✅ All dependencies imported")

except Exception as e:
    log_error(f"Watcher Crash during import: {e}")
    sys.exit(1)

print("Pre-flight check completed successfully.")
