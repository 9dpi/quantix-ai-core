from fastapi import APIRouter, HTTPException, Depends
from config.settings import settings
from schemas.signal import SignalOutput

router = APIRouter()

@router.post("/fx/signal", response_model=SignalOutput)
async def generate_signal(asset: str, timeframe: str = "M15"):
    # API Guard
    if settings.QUANTIX_MODE != "INTERNAL":
        raise HTTPException(status_code=403, detail="Public signal generation is not enabled")
        
    # Mock signal response
    return SignalOutput(
        asset=asset,
        direction="BUY",
        timeframe=timeframe,
        disclaimer="Internal research signal. Not financial advice."
    )
