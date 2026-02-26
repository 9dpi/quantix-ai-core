print("!!! MINIMAL APP STARTING !!!")
from fastapi import FastAPI
import uvicorn
import os
import sys

# Add backend to path
backend_path = os.path.join(os.getcwd(), "backend")
if os.path.exists(backend_path):
    sys.path.append(backend_path)
    os.environ["PYTHONPATH"] = backend_path

import socket

app = FastAPI()

@app.get("/")
async def root():
    return {
        "status": "minimal_online", 
        "port": os.getenv("PORT", "8080"),
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname())
    }

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    try:
        from quantix_core.database.connection import db
        from datetime import datetime, timezone
        db.client.table("fx_analysis_log").insert({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "asset": "DEBUG_MINIMAL",
            "direction": "STARTUP",
            "status": f"MINIMAL_ONLINE | Port: {os.getenv('PORT')} | Host: {socket.gethostname()}",
            "price": 0, "confidence": 1.0, "strength": 1.0
        }).execute()
        print("✅ Minimal app startup logged to DB")
    except Exception as e:
        print(f"❌ DB Log Failed: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting minimal app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
