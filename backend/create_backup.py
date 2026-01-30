"""
Manual Backup Script - Export fx_signals table before migration

This script exports current fx_signals data to JSON file as backup.
Run this BEFORE executing migration.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from loguru import logger

# Load environment
load_dotenv()

def create_backup():
    """Export fx_signals table to JSON backup file"""
    
    logger.info("=" * 60)
    logger.info("CREATING MANUAL BACKUP - fx_signals table")
    logger.info("=" * 60)
    
    # Initialize Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Missing SUPABASE_URL or SUPABASE_KEY")
        return False
    
    supabase = create_client(supabase_url, supabase_key)
    logger.success("✅ Connected to Supabase")
    
    # Fetch all signals
    logger.info("Fetching all fx_signals records...")
    
    try:
        response = supabase.table("fx_signals").select("*").execute()
        signals = response.data
        
        logger.info(f"Retrieved {len(signals)} signals")
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_fx_signals_{timestamp}.json"
        
        # Save to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({
                "backup_timestamp": datetime.now().isoformat(),
                "table": "fx_signals",
                "record_count": len(signals),
                "data": signals
            }, f, indent=2, default=str)
        
        logger.success(f"✅ Backup saved to: {backup_file}")
        logger.info(f"Records backed up: {len(signals)}")
        
        # Show sample
        if signals:
            logger.info("\nSample record (first signal):")
            sample = signals[0]
            for key in ['id', 'asset', 'direction', 'status', 'generated_at']:
                if key in sample:
                    logger.info(f"  {key}: {sample[key]}")
        
        logger.info("\n" + "=" * 60)
        logger.success("BACKUP COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Backup file: {backup_file}")
        logger.info(f"Records: {len(signals)}")
        logger.info("\n⚠️  Keep this file safe for rollback if needed!")
        
        return True
    
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

if __name__ == "__main__":
    success = create_backup()
    
    if success:
        print("\n✅ Backup created successfully!")
        print("You can now proceed with migration.")
    else:
        print("\n❌ Backup failed!")
        print("Do NOT proceed with migration until backup is successful.")
