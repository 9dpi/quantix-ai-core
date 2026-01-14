"""
Quantix AI - Integrated Flow Demo
PART A (Miner) -> PART B (Learning Lab)
"""

import sys
import os
import json
import pandas as pd
from loguru import logger

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quantix_core.miner.generator import SnapshotGenerator
from quantix_core.learning_lab.advisor import LabAdvisor

async def run_demo():
    logger.info("🚀 Starting Quantix AI Flow Demo")
    
    # 1. Load data from previous golden snapshot for reproduction
    snapshot_path = os.path.join(os.path.dirname(__file__), '..', 'snapshots', 'e2e_snapshot_2025-01-10_EURUSD_H4.json')
    if not os.path.exists(snapshot_path):
        logger.error("❌ Golden snapshot not found! Please run e2e test first.")
        return

    with open(snapshot_path) as f:
        data = json.load(f)
    
    # Extract candles to DataFrame
    candles = data['results']['resampling']['candles']
    df = pd.DataFrame(candles)
    # Ensure OHLC columns for engine
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 2. PART A: AUTO DATA MINER (Snapshot Generation)
    miner = SnapshotGenerator()
    snapshot = miner.generate_snapshot(
        asset=data['symbol'],
        timeframe=data['timeframe'],
        df=df
    )
    miner.save_to_analytics(snapshot)
    
    print("\n" + "="*50)
    print("💎 PART A: MINED SNAPSHOT (AUDITABLE EVIDENCE)")
    print(json.dumps(snapshot, indent=2))
    print("="*50 + "\n")

    # 3. PART B: LEARNING LAB (Decision Support Mapping)
    lab = LabAdvisor()
    signal = lab.advise(snapshot)
    
    print("\n" + "="*50)
    print("🧪 PART B: LEARNING LAB (EXPERIMENTAL BUY/SELL)")
    print(json.dumps(signal, indent=2))
    print("="*50 + "\n")

    logger.success("🏁 Demo flow complete.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_demo())
