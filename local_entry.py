import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from quantix_core.api.routes import health, lab_reference
from quantix_core.config.settings import settings

app = FastAPI(title="Quantix AI Local (Light)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(lab_reference.router, prefix=settings.API_PREFIX, tags=["Lab"])

@app.get("/")
def root():
    return {"mode": "local_light", "status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
