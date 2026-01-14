"""
Generate High-Quality Sample Data for Quantix Learning
=======================================================
Creates realistic EUR/USD M15 candles with proper:
- Session detection
- Spread simulation
- Volume patterns
- Quality scoring
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

def generate_learning_data(days=30, timeframe_minutes=15):
    """
    Generate high-quality sample data for Quantix.
    
    Args:
        days: Number of days of data to generate
        timeframe_minutes: Candle timeframe (default: 15 for M15)
    
    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, spread
    """
    
    print(f"📊 Generating {days} days of EUR/USD M15 data...")
    
    # Start from 30 days ago
    start_date = datetime.now(pytz.UTC) - timedelta(days=days)
    
    # Generate timestamps (only during trading hours)
    timestamps = []
    current = start_date
    
    while current < datetime.now(pytz.UTC):
        # Skip weekends
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            timestamps.append(current)
        current += timedelta(minutes=timeframe_minutes)
    
    print(f"   Generated {len(timestamps):,} candles")
    
    # Generate realistic price movement
    np.random.seed(42)
    
    base_price = 1.08500  # EUR/USD typical level
    prices = [base_price]
    
    for i in range(len(timestamps) - 1):
        # Determine session for volatility
        hour = timestamps[i].hour
        
        # London-NY overlap (13:00-16:00 UTC) = higher volatility
        if 13 <= hour < 16:
            volatility = 0.0008
        # London (7:00-16:00) or NY (13:00-22:00)
        elif (7 <= hour < 16) or (13 <= hour < 22):
            volatility = 0.0005
        # Asia session
        elif 0 <= hour < 7:
            volatility = 0.0003
        # Off hours
        else:
            volatility = 0.0002
        
        # Random walk with drift
        change = np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # Create OHLCV data
    data = []
    
    for i, (timestamp, close_price) in enumerate(zip(timestamps, prices)):
        # Determine session
        hour = timestamp.hour
        if 13 <= hour < 16:
            session = 'overlap'
            spread = 0.00015  # 1.5 pips (tight)
            volume = int(np.random.uniform(2000, 5000))
        elif 7 <= hour < 16:
            session = 'london'
            spread = 0.00018  # 1.8 pips
            volume = int(np.random.uniform(1500, 4000))
        elif 13 <= hour < 22:
            session = 'newyork'
            spread = 0.00017  # 1.7 pips
            volume = int(np.random.uniform(1800, 4500))
        elif 0 <= hour < 7:
            session = 'asia'
            spread = 0.00025  # 2.5 pips (wider)
            volume = int(np.random.uniform(800, 2000))
        else:
            session = 'off_hours'
            spread = 0.00035  # 3.5 pips (very wide)
            volume = int(np.random.uniform(300, 1000))
        
        # Generate OHLC from close
        open_price = prices[i-1] if i > 0 else close_price
        
        # High/Low with realistic wicks
        range_size = abs(close_price - open_price) * np.random.uniform(1.5, 2.5)
        high = max(open_price, close_price) + range_size * 0.3
        low = min(open_price, close_price) - range_size * 0.3
        
        data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'open': round(open_price, 5),
            'high': round(high, 5),
            'low': round(low, 5),
            'close': round(close_price, 5),
            'volume': volume,
            'spread': spread,
            'session': session
        })
    
    df = pd.DataFrame(data)
    
    print(f"✅ Data generation complete!")
    print(f"   Date range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print(f"   Total candles: {len(df):,}")
    print(f"   Sessions breakdown:")
    print(df['session'].value_counts().to_string())
    
    return df


def save_csv(df, filename='eurusd_m15_learning_data.csv'):
    """Save DataFrame to CSV."""
    # Remove session column (not needed in CSV for upload)
    df_export = df.drop(columns=['session', 'spread'])
    df_export.to_csv(filename, index=False)
    print(f"\n💾 Saved to: {filename}")
    print(f"   Ready for upload via Ingestion Portal")
    return filename


if __name__ == "__main__":
    print("=" * 70)
    print("QUANTIX AI CORE - LEARNING DATA GENERATOR")
    print("=" * 70)
    print()
    
    # Generate 30 days of data
    df = generate_learning_data(days=30)
    
    # Save to CSV
    filename = save_csv(df)
    
    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print(f"1. File created: {filename}")
    print(f"2. Go to: https://9dpi.github.io/quantix-ai-core/input.html")
    print(f"3. Upload this CSV file")
    print(f"4. Quantix will validate and store learning-ready candles")
    print(f"5. Check results at: https://9dpi.github.io/quantix-ai-core/inspect.html")
    print()
