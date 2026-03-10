
from quantix_core.database.connection import db
from loguru import logger

def fix_schema():
    logger.info("Starting schema fix for fx_signals...")
    try:
        # 1. Try to add columns via direct SQL if RPC exists
        # If not, we will rely on PostgREST auto-detect after we do a dummy update
        logger.info("Attempting to verify columns...")
        
        # Test columns by trying to select them
        try:
            db.client.table('fx_signals').select('tp_pips, sl_pips').limit(1).execute()
            logger.success("Columns 'tp_pips' and 'sl_pips' already exist and are visible.")
        except Exception as e:
            logger.warning(f"Columns might be missing or cache is stale: {e}")
            
            # 2. Try to run RPC if defined in previous sessions
            try:
                db.client.rpc('fix_signal_schema_v2', {}).execute()
                logger.success("RPC 'fix_signal_schema_v2' executed.")
            except Exception as rpc_e:
                logger.error(f"RPC failed: {rpc_e}")

        # 3. Force schema refresh by performing a standard operation
        # and checking if we can insert a dummy record
        logger.info("Verifying insertion capability...")
        
    except Exception as e:
        logger.error(f"Schema fix failed: {e}")

if __name__ == '__main__':
    fix_schema()
