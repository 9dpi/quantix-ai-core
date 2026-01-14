"""
OANDA Ingestion Worker - Orchestrates clean data feed
Append-only, replay-safe, auditable

Principle: Single responsibility, fail-safe, idempotent
"""

from typing import List, Dict
from loguru import logger

from ingestion.oanda_client import OandaClient
from ingestion.oanda_normalizer import OandaNormalizer
from database.connection import db


class OandaIngestionWorker:
    """
    Orchestrates OANDA data ingestion into clean feed.
    
    Workflow:
    1. Fetch from OANDA
    2. Normalize & validate
    3. Upsert to database (idempotent)
    4. Audit log
    """
    
    def __init__(self):
        self.client = OandaClient()
        self.normalizer = OandaNormalizer()
    
    async def ingest_latest(
        self,
        instrument: str = "EUR_USD",
        timeframe: str = "H4",
        count: int = 500
    ) -> Dict:
        """
        Ingest latest candles for an instrument/timeframe.
        
        This is the main entry point for scheduled workers.
        
        Args:
            instrument: OANDA instrument (e.g., "EUR_USD")
            timeframe: Timeframe (e.g., "H4")
            count: Number of candles to fetch
            
        Returns:
            Ingestion summary dict
        """
        logger.info(f"🔄 Starting ingestion: {instrument} @ {timeframe}")
        
        try:
            # Step 1: Fetch from OANDA
            raw_candles = self.client.get_latest_candles(
                instrument=instrument,
                granularity=timeframe,
                count=count
            )
            
            if not raw_candles:
                logger.warning("⚠️ No candles received from OANDA")
                return {
                    "status": "no_data",
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "fetched": 0,
                    "inserted": 0
                }
            
            # Step 2: Normalize & validate
            normalized = self.normalizer.normalize_batch(
                raw_candles,
                instrument,
                timeframe
            )
            
            if not normalized:
                logger.warning("⚠️ No complete candles after normalization")
                return {
                    "status": "no_complete_candles",
                    "instrument": instrument,
                    "timeframe": timeframe,
                    "fetched": len(raw_candles),
                    "inserted": 0
                }
            
            # Step 3: Upsert to database (idempotent)
            inserted = await self._upsert_candles(normalized)
            
            logger.info(f"✅ Ingestion complete: {inserted}/{len(normalized)} candles inserted")
            
            return {
                "status": "success",
                "instrument": instrument,
                "timeframe": timeframe,
                "fetched": len(raw_candles),
                "normalized": len(normalized),
                "inserted": inserted
            }
            
        except Exception as e:
            logger.error(f"❌ Ingestion failed: {e}")
            return {
                "status": "error",
                "instrument": instrument,
                "timeframe": timeframe,
                "error": str(e)
            }
    
    async def _upsert_candles(self, candles: List[Dict]) -> int:
        """
        Upsert candles to database (idempotent).
        
        Uses ON CONFLICT DO NOTHING for idempotency.
        
        Args:
            candles: List of normalized candles
            
        Returns:
            Number of candles inserted (not updated)
        """
        if not candles:
            return 0
        
        inserted_count = 0
        
        for candle in candles:
            try:
                # Use Supabase upsert (idempotent)
                result = db.client.table('market_candles_v1').upsert(
                    candle,
                    on_conflict='provider,instrument,timeframe,timestamp'
                ).execute()
                
                # Check if actually inserted (not just matched)
                if result.data:
                    inserted_count += 1
                    
            except Exception as e:
                logger.error(f"❌ Failed to insert candle {candle.get('timestamp')}: {e}")
                continue
        
        return inserted_count
    
    async def backfill(
        self,
        instrument: str = "EUR_USD",
        timeframe: str = "H4",
        total_candles: int = 5000
    ) -> Dict:
        """
        Backfill historical data.
        
        Fetches in batches to respect OANDA limits.
        
        Args:
            instrument: OANDA instrument
            timeframe: Timeframe
            total_candles: Total candles to backfill
            
        Returns:
            Backfill summary
        """
        logger.info(f"📚 Starting backfill: {instrument} @ {timeframe} ({total_candles} candles)")
        
        batch_size = 500  # OANDA safe batch size
        batches = (total_candles + batch_size - 1) // batch_size
        
        total_inserted = 0
        
        for i in range(batches):
            logger.info(f"📦 Backfill batch {i+1}/{batches}")
            
            result = await self.ingest_latest(
                instrument=instrument,
                timeframe=timeframe,
                count=batch_size
            )
            
            total_inserted += result.get('inserted', 0)
            
            # Small delay to avoid rate limits
            import asyncio
            await asyncio.sleep(1)
        
        logger.info(f"✅ Backfill complete: {total_inserted} total candles")
        
        return {
            "status": "success",
            "instrument": instrument,
            "timeframe": timeframe,
            "total_inserted": total_inserted,
            "batches": batches
        }
