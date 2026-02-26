
from fastapi import FastAPI
import uvicorn
import os
from datetime import datetime, timezone

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "minimal_ok", "time": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting MINIMAL server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
