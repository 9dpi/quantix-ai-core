import sys
from loguru import logger

sys.stdout.reconfigure(encoding='utf-8')

def check_data_feed():
    try:
        from quantix_core.database.connection import db
        res = db.client.table('fx_analysis_log').select('timestamp,status').eq('asset', 'ANALYZER_LOG').like('status', '%Data Source%').order('timestamp', desc=True).limit(10).execute()
        
        print("--- RECENT MARKET DATA SOURCES ---")
        if not res.data:
            print("No data source logs found recently.")
        else:
            for r in res.data:
                # status is like: "2026-03-06 00:40:03.095 | INFO     | __main__:run_cycle:207 - 📡 Data Source: TWELVEDATA"
                msg = str(r['status']).split('- ')[-1] if '- ' in str(r['status']) else str(r['status'])
                print(f"[{r['timestamp'][:19]}] {msg.strip()}")
                
    except Exception as e:
        print(f"Error checking data feed: {e}")

if __name__ == "__main__":
    check_data_feed()
