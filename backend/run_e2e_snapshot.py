"""
Simplified E2E Test - Run this locally and paste results

Usage:
    python backend/run_e2e_snapshot.py

This will:
1. Test Dukascopy download
2. Test tick parsing
3. Test candle resampling
4. Test validation
5. Call Structure API
6. Generate JSON snapshot
"""

import asyncio
import json
from datetime import datetime
from loguru import logger
import sys

# Add parent directory to path
sys.path.insert(0, '.')

from ingestion.dukascopy.client import DukascopyClient
from ingestion.dukascopy.tick_parser import TickParser
from ingestion.dukascopy.resampler import CandleResampler
from ingestion.dukascopy.validator import CandleValidator


async def run_snapshot_test():
    """
    Run E2E test and generate snapshot.
    
    This tests the pipeline WITHOUT database:
    Dukascopy → Ticks → Candles → Validation
    """
    logger.info("=" * 80)
    logger.info("QUANTIX AI - E2E SNAPSHOT TEST")
    logger.info("=" * 80)
    logger.info("")
    
    snapshot = {
        "test_date": "2025-01-10",
        "symbol": "EURUSD",
        "timeframe": "H4",
        "results": {}
    }
    
    try:
        # Step 1: Download ticks
        logger.info("STEP 1: Downloading Dukascopy ticks...")
        client = DukascopyClient()
        test_date = datetime(2025, 1, 10)  # Friday
        
        tick_chunks = client.download_day_ticks("EURUSD", test_date)
        
        snapshot["results"]["download"] = {
            "status": "success",
            "chunks_received": len(tick_chunks),
            "expected_chunks": 24
        }
        
        logger.info(f"✅ Downloaded {len(tick_chunks)} hour chunks")
        
        # Step 2: Parse ticks
        logger.info("")
        logger.info("STEP 2: Parsing ticks...")
        parser = TickParser()
        all_ticks = []
        
        for hour, chunk in enumerate(tick_chunks):
            hour_start = test_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            ticks = parser.parse_ticks(chunk, hour_start)
            all_ticks.extend(ticks)
        
        snapshot["results"]["parsing"] = {
            "status": "success",
            "total_ticks": len(all_ticks),
            "first_tick_timestamp": all_ticks[0].timestamp.isoformat() if all_ticks else None,
            "last_tick_timestamp": all_ticks[-1].timestamp.isoformat() if all_ticks else None,
            "first_tick_bid": float(all_ticks[0].bid) if all_ticks else None
        }
        
        logger.info(f"✅ Parsed {len(all_ticks)} ticks")
        logger.info(f"   First tick: {all_ticks[0].timestamp} @ {all_ticks[0].bid}")
        logger.info(f"   Last tick: {all_ticks[-1].timestamp} @ {all_ticks[-1].bid}")
        
        # Step 3: Resample to H4
        logger.info("")
        logger.info("STEP 3: Resampling to H4 candles...")
        resampler = CandleResampler()
        candles = resampler.resample_h4(all_ticks)
        
        snapshot["results"]["resampling"] = {
            "status": "success",
            "candles_created": len(candles),
            "expected_candles": 6,
            "candles": []
        }
        
        for candle in candles:
            snapshot["results"]["resampling"]["candles"].append({
                "timestamp": candle.timestamp.isoformat(),
                "open": float(candle.open),
                "high": float(candle.high),
                "low": float(candle.low),
                "close": float(candle.close),
                "tick_count": candle.tick_count,
                "complete": candle.complete
            })
        
        logger.info(f"✅ Created {len(candles)} H4 candles")
        for i, candle in enumerate(candles):
            logger.info(
                f"   Candle {i+1}: {candle.timestamp} | "
                f"O:{candle.open:.5f} H:{candle.high:.5f} L:{candle.low:.5f} C:{candle.close:.5f} | "
                f"Ticks:{candle.tick_count} Complete:{candle.complete}"
            )
        
        # Step 4: Validate
        logger.info("")
        logger.info("STEP 4: Validating candles...")
        validator = CandleValidator("H4")
        valid_candles, invalid_candles = validator.validate_batch(candles)
        
        snapshot["results"]["validation"] = {
            "status": "success",
            "valid_candles": len(valid_candles),
            "invalid_candles": len(invalid_candles),
            "validation_rate": len(valid_candles) / len(candles) if candles else 0
        }
        
        logger.info(f"✅ Validation: {len(valid_candles)} valid, {len(invalid_candles)} invalid")
        
        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("SNAPSHOT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Date: {test_date.date()}")
        logger.info(f"Symbol: EURUSD")
        logger.info(f"Timeframe: H4")
        logger.info(f"Ticks parsed: {len(all_ticks)}")
        logger.info(f"Candles created: {len(candles)}")
        logger.info(f"Candles valid: {len(valid_candles)}")
        logger.info(f"Complete candles: {sum(1 for c in candles if c.complete)}")
        logger.info("")
        
        # Save snapshot
        snapshot_file = "e2e_snapshot.json"
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot, f, indent=2)
        
        logger.info(f"📸 Snapshot saved to: {snapshot_file}")
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ E2E SNAPSHOT TEST COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("NEXT STEPS:")
        logger.info("1. Review e2e_snapshot.json")
        logger.info("2. Paste snapshot JSON to confirm")
        logger.info("3. Test Structure API with real data")
        
        return snapshot
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        snapshot["results"]["error"] = {
            "status": "failed",
            "error": str(e)
        }
        
        return snapshot


if __name__ == "__main__":
    snapshot = asyncio.run(run_snapshot_test())
    
    print("\n" + "=" * 80)
    print("SNAPSHOT JSON (paste this):")
    print("=" * 80)
    print(json.dumps(snapshot, indent=2))
