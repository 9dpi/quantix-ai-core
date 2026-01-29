"""
Strength Validation Monitor
Tracks correlation between strength metric and signal outcomes
"""

import asyncio
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings
import pandas as pd

async def monitor_strength_validation():
    """
    Monitor first 10-20 signals to validate strength metric.
    
    Hypothesis:
    - Low strength (< 0.5) → Higher fakeout rate
    - High strength (> 0.7) → Better follow-through
    """
    
    print("=" * 80)
    print("🔬 STRENGTH VALIDATION MONITOR")
    print("=" * 80)
    print()
    
    try:
        # Fetch recent analysis logs with strength data
        res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
            .select("*")\
            .order("timestamp", desc=True)\
            .limit(50)\
            .execute()
        
        if not res.data:
            print("⚠️ No data found in analysis log")
            return
        
        df = pd.DataFrame(res.data)
        
        # Filter only entries with strength data
        df_with_strength = df[df['strength'].notna()].copy()
        
        if len(df_with_strength) == 0:
            print("⚠️ No entries with strength data yet")
            print(f"Total entries: {len(df)}")
            return
        
        print(f"📊 Total Analysis Entries: {len(df)}")
        print(f"📊 Entries with Strength: {len(df_with_strength)}")
        print()
        
        # Convert timestamp to datetime
        df_with_strength['timestamp'] = pd.to_datetime(df_with_strength['timestamp'])
        
        # Categorize by strength
        df_with_strength['strength_category'] = pd.cut(
            df_with_strength['strength'],
            bins=[0, 0.5, 0.7, 1.0],
            labels=['Low (0-50%)', 'Medium (50-70%)', 'High (70-100%)']
        )
        
        print("🎯 STRENGTH DISTRIBUTION")
        print("-" * 80)
        strength_dist = df_with_strength['strength_category'].value_counts()
        for category, count in strength_dist.items():
            pct = (count / len(df_with_strength)) * 100
            print(f"  {category}: {count} signals ({pct:.1f}%)")
        print()
        
        # Show recent signals with strength
        print("📋 RECENT SIGNALS (Latest 20 with Strength)")
        print("-" * 80)
        print(f"{'Timestamp':<20} {'Direction':<8} {'Conf%':<7} {'Str%':<7} {'Price':<10} {'Category':<20}")
        print("-" * 80)
        
        recent = df_with_strength.head(20)
        for _, row in recent.iterrows():
            ts = row['timestamp'].strftime('%Y-%m-%d %H:%M')
            direction = row['direction']
            conf_pct = f"{row['confidence']*100:.1f}%"
            str_pct = f"{row['strength']*100:.1f}%"
            price = f"{row['price']:.5f}"
            category = row['strength_category']
            
            print(f"{ts:<20} {direction:<8} {conf_pct:<7} {str_pct:<7} {price:<10} {category:<20}")
        
        print()
        print("=" * 80)
        print("📈 VALIDATION INSIGHTS")
        print("=" * 80)
        
        # Calculate average strength by direction
        avg_by_direction = df_with_strength.groupby('direction')['strength'].agg(['mean', 'count'])
        print("\n🔍 Average Strength by Direction:")
        for direction, row in avg_by_direction.iterrows():
            print(f"  {direction}: {row['mean']:.2f} (n={int(row['count'])})")
        
        # Calculate average confidence by strength category
        if 'strength_category' in df_with_strength.columns:
            avg_conf_by_strength = df_with_strength.groupby('strength_category')['confidence'].mean()
            print("\n🔍 Average Confidence by Strength Category:")
            for category, avg_conf in avg_conf_by_strength.items():
                print(f"  {category}: {avg_conf:.2f}")
        
        print()
        print("=" * 80)
        print("💡 NEXT STEPS FOR VALIDATION")
        print("=" * 80)
        print("1. Monitor next 10-20 signals as they occur")
        print("2. Track price movement 10-30 candles after signal")
        print("3. Compare:")
        print("   - Low strength signals: Did they reverse/fakeout?")
        print("   - High strength signals: Did they follow through?")
        print("4. Document findings before making rule changes")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(monitor_strength_validation())
