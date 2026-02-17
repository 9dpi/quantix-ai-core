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
        
        # 3. Discrepancy Breakdown with Percentages
        entry_m = len(discrepancies[discrepancies['check_type'] == 'ENTRY_MISMATCH']) if not discrepancies.empty else 0
        tp_m = len(discrepancies[discrepancies['check_type'] == 'TP_MISMATCH']) if not discrepancies.empty else 0
        sl_m = len(discrepancies[discrepancies['check_type'] == 'SL_MISMATCH']) if not discrepancies.empty else 0
        
        def get_pct(val):
            return (val / total_events * 100) if total_events > 0 else 0

        # 4. Spread Impact & Max Drift
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
                        # Convert to pips (assuming 5 decimal places for EURUSD)
                        drifts.append(abs(float(row['validator_price']) - float(target)) * 10000)
                except: continue
        
        avg_drift = sum(drifts) / len(drifts) if drifts else 0
        max_drift = max(drifts) if drifts else 0
        
        # 5. Conclusion & Recommendation Logic
        discrepancy_rate = (total_discrepancies / total_events * 100) if total_events > 0 else 0
        
        if total_events == 0:
            conclusion = "Incomplete data"
            recommendation = "Wait for more market events"
        elif discrepancy_rate < 5:
            conclusion = f"Binance proxy is {(100-discrepancy_rate):.1f}% accurate"
            recommendation = "STAY with current setup (Add spread buffer)"
        elif discrepancy_rate < 10:
            conclusion = "Moderate discrepancies detected"
            recommendation = "CONSIDER Phase 2 (Pepperstone Feed)"
        else:
            conclusion = "High discrepancy rate detected"
            recommendation = "PROCEED to Phase 2 immediately"

        # --- REPORT GENERATION ---
        report = [
            ["Metric", "Value", "%"],
            ["Total signals validated", unique_signals, "-"],
            ["Total validation events", total_events, "-"],
            ["Entry mismatches", entry_m, f"{get_pct(entry_m):.1f}%"],
            ["TP mismatches", tp_m, f"{get_pct(tp_m):.1f}%"],
            ["SL mismatches", sl_m, f"{get_pct(sl_m):.1f}%"],
            ["Average discrepancy", f"{avg_drift:.2f} pips", "-"],
            ["Max discrepancy", f"{max_drift:.2f} pips", "-"],
        ]
        
        print("\n" + "="*55)
        print(f"   VALIDATION REPORT ({days} days) - Automated Analysis")
        print("="*55)
        print(tabulate(report, headers="firstrow", tablefmt="fancy_grid"))
        print(f" CONCLUSION: {conclusion}")
        print(f" RECOMMENDATION: {recommendation}")
        print("="*55 + "\n")
        
        return df

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return None

if __name__ == "__main__":
    run_analysis()
