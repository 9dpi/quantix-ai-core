"""
Database Migration Runner: v1 → v2 State Machine
Executes the migration script on Supabase database
"""

import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_supabase_client() -> Client:
    """Initialize Supabase client"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def read_migration_script() -> str:
    """Read the migration SQL script"""
    script_path = Path(__file__).parent / "supabase" / "007_migration_v1_to_v2.sql"
    
    if not script_path.exists():
        raise FileNotFoundError(f"Migration script not found: {script_path}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_migration(client: Client, sql_script: str) -> bool:
    """
    Execute migration script on Supabase
    
    Note: Supabase Python client doesn't support raw SQL execution directly.
    This function provides the SQL for manual execution via Supabase Dashboard.
    """
    logger.warning("⚠️  Supabase Python client doesn't support raw SQL execution")
    logger.info("📋 Please execute the migration manually via Supabase Dashboard:")
    logger.info("   1. Go to: https://app.supabase.com/project/YOUR_PROJECT/sql")
    logger.info("   2. Copy the SQL from: supabase/007_migration_v1_to_v2.sql")
    logger.info("   3. Paste and run in the SQL Editor")
    
    return False

def verify_migration(client: Client) -> bool:
    """Verify migration was successful"""
    try:
        # Check if new columns exist by querying a signal
        response = client.table('fx_signals').select('state, entry_price, expiry_at').limit(1).execute()
        
        if response.data:
            logger.success("✅ Migration verification passed - new columns exist")
            return True
        else:
            logger.warning("⚠️  No data to verify, but schema appears updated")
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration verification failed: {e}")
        return False

def check_state_distribution(client: Client):
    """Check distribution of signals across states"""
    try:
        # Note: Supabase client doesn't support GROUP BY directly
        # This would need to be done via RPC or manual query
        logger.info("📊 State Distribution Check:")
        logger.info("   Run this query manually in Supabase SQL Editor:")
        logger.info("   SELECT state, COUNT(*) FROM fx_signals GROUP BY state;")
        
    except Exception as e:
        logger.error(f"Error checking state distribution: {e}")

def main():
    """Main migration runner"""
    logger.info("🚀 Starting Database Migration: v1 → v2")
    
    # Initialize client
    try:
        client = get_supabase_client()
        logger.success("✅ Connected to Supabase")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Supabase: {e}")
        return
    
    # Read migration script
    try:
        sql_script = read_migration_script()
        logger.success(f"✅ Loaded migration script ({len(sql_script)} bytes)")
    except Exception as e:
        logger.error(f"❌ Failed to load migration script: {e}")
        return
    
    # Execute migration (manual step)
    logger.info("=" * 60)
    logger.info("MANUAL MIGRATION REQUIRED")
    logger.info("=" * 60)
    execute_migration(client, sql_script)
    
    # Wait for user confirmation
    input("\n⏸️  Press Enter after you've executed the migration in Supabase Dashboard...")
    
    # Verify migration
    logger.info("\n🔍 Verifying migration...")
    if verify_migration(client):
        logger.success("✅ Migration completed successfully!")
        check_state_distribution(client)
    else:
        logger.error("❌ Migration verification failed")

if __name__ == "__main__":
    main()
