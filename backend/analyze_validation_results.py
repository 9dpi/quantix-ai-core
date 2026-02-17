import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger
from tabulate import tabulate

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from quantix_core.database.connection import db

def run_analysis(days=14):
    """
    Analyze validation performance metrics for the last N days
    """
    logger.info(f"📊 Running Validation Performance Analysis (Last {days} days)...")
    
    try:
        # 1. Fetch data from Supabase
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        res = db.client.table("validation_events")\
            .select("*")\
            .gte("created_at", start_date)\
            .execute()
        
        data = res.data
        if not data:
            logger.warning("No validation data found for the selected period.")
            return

        df = pd.DataFrame(data)
        
        # 2. Basic Metrics
        total_events = len(df)
        unique_signals = df['signal_id'].nunique()
        discrepancies = df[df['is_discrepancy'] == True]
        total_discrepancies = len(discrepancies)
        
        # 3. Discrepancy Breakdown
        breakdown = discrepancies['check_type'].value_counts().to_dict() if not discrepancies.empty else {}
        
        # 4. Spread Impact (Estimation)
        # Note: validator_price is the market price at validation time
        # We can calculate the 'drift' if meta_data contains the target price
        drifts = []
        for _, row in df.iterrows():
            if row['is_discrepancy'] and row['meta_data']:
                try:
                    meta = row['meta_data']
                    target = None
                    if row['check_type'] == 'ENTRY': target = meta.get('entry_price')
                    elif row['check_type'] == 'TP': target = meta.get('tp_price') or meta.get('tp')
                    elif row['check_type'] == 'SL': target = meta.get('sl_price') or meta.get('sl')
                    
                    if target and row['validator_price']:
                        drifts.append(abs(float(row['validator_price']) - float(target)))
                except:
                    continue
        
        avg_drift = sum(drifts) / len(drifts) if drifts else 0
        
        # 5. Resource Usage (Current Process)
        import psutil
        process = psutil.Process(os.getpid())
        mem_mb = process.memory_info().rss / (1024 * 1024)
        
        # --- REPORT GENERATION ---
        report = [
            ["Metric", "Value"],
            ["Total Signals Validated", unique_signals],
            ["Total Validation Events", total_events],
            ["Total Discrepancies", f"{total_discrepancies} ({(total_discrepancies/total_events*100):.1f}%)" if total_events > 0 else 0],
            ["- Entry Mismatches", breakdown.get('ENTRY_MISMATCH', 0)],
            ["- TP Mismatches", breakdown.get('TP_MISMATCH', 0)],
            ["- SL Mismatches", breakdown.get('SL_MISMATCH', 0)],
            ["Average Spread Drift", f"{avg_drift:.5f} units"],
            ["Current Memory Usage", f"{mem_mb:.1f} MB"],
            ["Analysis Period", f"{days} days"]
        ]
        
        print("\n" + "="*50)
        print("   QUANTIX VALIDATION PERFORMANCE REPORT")
        print("="*50)
        print(tabulate(report, headers="firstrow", tablefmt="fancy_grid"))
        print("="*50 + "\n")
        
        return df

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None

if __name__ == "__main__":
    run_analysis()
