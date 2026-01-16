from fastapi import FastAPI
from typing import Optional

app = FastAPI()

class Item:
    name: str
    price: Optional[float] = None

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
