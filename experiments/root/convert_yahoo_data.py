"""
Convert Yahoo Finance EUR/USD data to Quantix format and upload
================================================================
Takes daily OHLC data and prepares it for Quantix ingestion
"""

import pandas as pd
from datetime import datetime

# Yahoo Finance EUR/USD Daily Data (from your screenshot)
data = {
    'Date': [
        'Jan 14, 2026', 'Jan 13, 2026', 'Jan 12, 2026', 'Jan 9, 2026', 'Jan 8, 2026',
        'Jan 7, 2026', 'Jan 6, 2026', 'Jan 5, 2026', 'Jan 2, 2026', 'Dec 31, 2025',
        'Dec 30, 2025', 'Dec 29, 2025', 'Dec 26, 2025', 'Dec 24, 2025', 'Dec 23, 2025',
        'Dec 22, 2025', 'Dec 19, 2025', 'Dec 18, 2025', 'Dec 17, 2025', 'Dec 16, 2025',
        'Dec 15, 2025', 'Dec 12, 2025'
    ],
    'Open': [
        1.1647, 1.1668, 1.1625, 1.1658, 1.1677, 1.1688, 1.1716, 1.1706, 1.1751, 1.1746,
        1.1773, 1.1775, 1.1784, 1.1796, 1.1764, 1.1711, 1.1725, 1.1742, 1.1750, 1.1755,
        1.1738, 1.1741
    ],
    'High': [
        1.1663, 1.1675, 1.1699, 1.1660, 1.1685, 1.1705, 1.1745, 1.1719, 1.1767, 1.1759,
        1.1781, 1.1789, 1.1799, 1.1809, 1.1804, 1.1770, 1.1738, 1.1759, 1.1758, 1.1805,
        1.1769, 1.1747
    ],
    'Low': [
        1.1640, 1.1635, 1.1623, 1.1619, 1.1653, 1.1674, 1.1684, 1.1660, 1.1713, 1.1721,
        1.1746, 1.1754, 1.1763, 1.1774, 1.1764, 1.1711, 1.1704, 1.1713, 1.1705, 1.1746,
        1.1727, 1.1720
    ],
    'Close': [
        1.1651, 1.1667, 1.1624, 1.1658, 1.1677, 1.1688, 1.1715, 1.1705, 1.1750, 1.1747,
        1.1773, 1.1773, 1.1785, 1.1796, 1.1766, 1.1708, 1.1726, 1.1742, 1.1750, 1.1755,
        1.1738, 1.1739
    ]
}

def convert_to_quantix_format():
    """Convert Yahoo Finance data to Quantix CSV format."""
    
    print("=" * 70)
    print("CONVERTING YAHOO FINANCE DATA TO QUANTIX FORMAT")
    print("=" * 70)
    print()
    
    df = pd.DataFrame(data)
    
    # Convert date format
    df['timestamp'] = pd.to_datetime(df['Date'], format='%b %d, %Y')
    df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%d 00:00:00')
    
    # Rename columns to match Quantix format
    df_quantix = pd.DataFrame({
        'timestamp': df['timestamp'],
        'open': df['Open'],
        'high': df['High'],
        'low': df['Low'],
        'close': df['Close'],
        'volume': 0  # Yahoo Finance doesn't provide volume for forex
    })
    
    # Sort by date (oldest first)
    df_quantix = df_quantix.sort_values('timestamp')
    
    # Save to CSV
    filename = 'eurusd_yahoo_finance.csv'
    df_quantix.to_csv(filename, index=False)
    
    print(f"✅ Conversion complete!")
    print(f"   Total candles: {len(df_quantix)}")
    print(f"   Date range: {df_quantix['timestamp'].iloc[0]} to {df_quantix['timestamp'].iloc[-1]}")
    print(f"   Saved to: {filename}")
    print()
    
    # Show sample
    print("Sample data (first 5 rows):")
    print(df_quantix.head().to_string(index=False))
    print()
    
    return filename


if __name__ == "__main__":
    filename = convert_to_quantix_format()
    
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print(f"1. ✅ File created: {filename}")
    print(f"2. Go to: https://9dpi.github.io/quantix-ai-core/input.html")
    print(f"3. Upload this CSV file")
    print(f"4. Asset: EURUSD")
    print(f"5. Timeframe: D1 (Daily)")
    print(f"6. Click 'EXECUTE INGESTION SEQUENCE'")
    print()
    print("After upload, check:")
    print("   https://9dpi.github.io/quantix-ai-core/inspect.html")
    print()
