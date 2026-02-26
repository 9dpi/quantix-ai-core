from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "minimal_online", "port": os.getenv("PORT", "8080")}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    print(f"Starting minimal app on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
