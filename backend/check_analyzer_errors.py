import sys
import json
from datetime import datetime
from loguru import logger
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

sys.stdout.reconfigure(encoding='utf-8')

def check_analyzer_errors():
    try:
        from quantix_core.database.connection import db
        
        # Pull the last 50 logs from ANALYZER_LOG
        res = db.client.table('fx_analysis_log').select('status,timestamp').eq('asset', 'ANALYZER_LOG').order('timestamp', desc=True).limit(50).execute()
        
        if not res.data:
            print("No recent analyzer logs found.")
            return

        error_keywords = ["error", "fail", "exception", "traceback", "pgrst"]
        
        errors_found = []
        for row in res.data:
            status_text = str(row.get('status', ''))
            status_lower = status_text.lower()
            
            # Check for error keywords
            if any(kw in status_lower for kw in error_keywords):
                # Filter out intentional or non-critical logs if necessary, 
                # but generally if it says "FAIL", we want to know.
                errors_found.append((row['timestamp'], status_text))

        print(f"--- ANALYZER ERROR SCAN (Last 50 Engine Logs) ---")
        if not errors_found:
            print("✅ SYSTEM HEALTHY: No backend engine errors detected in recent logs.")
        else:
            print(f"❌ WARNING: Found {len(errors_found)} error occurrences in recent logs!")
            for idx, (ts, err) in enumerate(errors_found[:5]): # Show up to 5
                # Trim the error to be readable
                err_short = err[:150] + ("..." if len(err) > 150 else "")
                print(f"   [{idx+1}] {ts[11:19]} UTC | {err_short}")
                
            if len(errors_found) > 5:
                print(f"   ... and {len(errors_found) - 5} more errors.")
                
    except Exception as e:
        print(f"❌ SCANNED FAILED: {e}")

if __name__ == "__main__":
    check_analyzer_errors()
