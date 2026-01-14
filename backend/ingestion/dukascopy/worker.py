"""
Dukascopy Ingestion Worker - Dumb Orchestrator
Pipeline: download → parse → resample → validate → persist

Principle: No logic, just orchestration. Idempotent, resume-safe.
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid
from loguru import logger

from ingestion.dukascopy.client import DukascopyClient
from ingestion.dukascopy.tick_parser import TickParser
from ingestion.dukascopy.resampler import CandleResampler, Candle
from ingestion.dukascopy.validator import CandleValidator
from database.connection import db


class DukascopyWorker:
    """
    Orchestrates Dukascopy data ingestion pipeline.
    
    Responsibilities:
    1. Download tick data
    2. Parse ticks
    3. Resample to candles
    4. Validate candles
    5. Persist to market_candles_v1
    
    Does NOT:
    - Touch Structure Engine
    - Make decisions about validity
    - Fix/fill data
    """
    
    def __init__(self):
        self.client = DukascopyClient()
        self.parser = TickParser()
        self.resampler = CandleResampler()
    
    async def ingest_day(
        self,
        symbol: str,
        date: datetime,
        timeframe: str = "H4"
    ) -> Dict:
        """
        Ingest one day of data.
        
        Args:
            symbol: Quantix symbol (e.g., "EURUSD")
            date: Date to ingest
            timeframe: Target timeframe (H4 or D1)
            
        Returns:
            Ingestion summary
        """
        trace_id = f"duka-{uuid.uuid4().hex[:8]}"
        
        logger.info(
            f"[{trace_id}] 🔄 Ingesting {symbol} {date.date()} @ {timeframe}"
        )
        
        try:
            # Step 1: Download tick data
            tick_chunks = self.client.download_day_ticks(symbol, date)
            
            if not tick_chunks:
                logger.warning(f"[{trace_id}] No tick data for {date.date()}")
                return {
                    "status": "no_data",
                    "symbol": symbol,
                    "date": date.date(),
                    "timeframe": timeframe,
                    "trace_id": trace_id
                }
            
            # Step 2: Parse ticks
            all_ticks = []
            for hour, chunk in enumerate(tick_chunks):
                hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                try:
                    ticks = self.parser.parse_ticks(chunk, hour_start)
                    all_ticks.extend(ticks)
                except ValueError as e:
                    logger.error(f"[{trace_id}] Parse error hour {hour}: {e}")
                    # FAIL HARD on parse error
                    return {
                        "status": "parse_error",
                        "symbol": symbol,
                        "date": date.date(),
                        "error": str(e),
                        "trace_id": trace_id
                    }
            
            logger.info(f"[{trace_id}] Parsed {len(all_ticks)} ticks")
            
            # Step 3: Resample to candles
            if timeframe == "H4":
                candles = self.resampler.resample_h4(all_ticks)
            elif timeframe == "D1":
                candles = self.resampler.resample_d1(all_ticks)
            else:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
            
            logger.info(f"[{trace_id}] Resampled to {len(candles)} candles")
            
            # Step 4: Validate candles
            validator = CandleValidator(timeframe)
            valid_candles, invalid_candles = validator.validate_batch(candles)
            
            if invalid_candles:
                logger.warning(
                    f"[{trace_id}] Dropped {len(invalid_candles)} invalid candles"
                )
            
            # Validate sequence
            if valid_candles:
                seq_errors = validator.validate_sequence(valid_candles)
                if seq_errors:
                    logger.error(f"[{trace_id}] Sequence errors: {seq_errors}")
                    # FAIL HARD on sequence violation
                    return {
                        "status": "sequence_error",
                        "symbol": symbol,
                        "date": date.date(),
                        "errors": seq_errors,
                        "trace_id": trace_id
                    }
            
            # Step 5: Persist to database
            if valid_candles:
                inserted = await self._persist_candles(
                    valid_candles,
                    symbol,
                    timeframe,
                    trace_id
                )
                
                logger.info(
                    f"[{trace_id}] ✅ Ingestion complete: "
                    f"{inserted}/{len(valid_candles)} candles persisted"
                )
                
                return {
                    "status": "success",
                    "symbol": symbol,
                    "date": date.date(),
                    "timeframe": timeframe,
                    "ticks_parsed": len(all_ticks),
                    "candles_created": len(candles),
                    "candles_valid": len(valid_candles),
                    "candles_persisted": inserted,
                    "trace_id": trace_id
                }
            else:
                logger.warning(f"[{trace_id}] No valid candles to persist")
                return {
                    "status": "no_valid_candles",
                    "symbol": symbol,
                    "date": date.date(),
                    "trace_id": trace_id
                }
            
        except Exception as e:
            logger.error(f"[{trace_id}] ❌ Ingestion failed: {e}")
            return {
                "status": "error",
                "symbol": symbol,
                "date": date.date(),
                "error": str(e),
                "trace_id": trace_id
            }
    
    async def _persist_candles(
        self,
        candles: List[Candle],
        symbol: str,
        timeframe: str,
        trace_id: str
    ) -> int:
        """
        Persist candles to market_candles_v1.
        
        Idempotent: Uses UNIQUE constraint on (provider, instrument, timeframe, timestamp)
        
        Args:
            candles: List of validated candles
            symbol: Symbol
            timeframe: Timeframe
            trace_id: Trace ID for logging
            
        Returns:
            Number of candles actually inserted (not updated)
        """
        inserted_count = 0
        
        for candle in candles:
            # Build record
            record = {
                "provider": "dukascopy",
                "instrument": symbol,
                "timeframe": timeframe,
                "timestamp": candle.timestamp.isoformat(),
                "open": float(candle.open),
                "high": float(candle.high),
                "low": float(candle.low),
                "close": float(candle.close),
                "volume": int(candle.volume),
                "complete": candle.complete,
                "source_id": f"dukascopy:{symbol}:{timeframe}:{candle.timestamp.isoformat()}"
            }
            
            try:
                # Idempotent upsert
                result = db.client.table('market_candles_v1').upsert(
                    record,
                    on_conflict='provider,instrument,timeframe,timestamp'
                ).execute()
                
                if result.data:
                    inserted_count += 1
                    
            except Exception as e:
                logger.error(
                    f"[{trace_id}] Failed to persist candle "
                    f"{candle.timestamp}: {e}"
                )
                continue
        
        return inserted_count
    
    async def backfill(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "H4"
    ) -> Dict:
        """
        Backfill historical data.
        
        Resume-safe: Processes day by day, each day is atomic.
        
        Args:
            symbol: Symbol to backfill
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            timeframe: Target timeframe
            
        Returns:
            Backfill summary
        """
        logger.info(
            f"📚 Backfilling {symbol} @ {timeframe} "
            f"from {start_date.date()} to {end_date.date()}"
        )
        
        current_date = start_date
        total_candles = 0
        total_days = 0
        errors = []
        
        while current_date <= end_date:
            result = await self.ingest_day(symbol, current_date, timeframe)
            
            if result["status"] == "success":
                total_candles += result.get("candles_persisted", 0)
                total_days += 1
            elif result["status"] != "no_data":
                errors.append({
                    "date": current_date.date(),
                    "error": result.get("error", result["status"])
                })
            
            current_date += timedelta(days=1)
        
        logger.info(
            f"✅ Backfill complete: {total_candles} candles "
            f"across {total_days} days"
        )
        
        return {
            "status": "complete",
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date.date(),
            "end_date": end_date.date(),
            "total_days_processed": total_days,
            "total_candles": total_candles,
            "errors": errors
        }
