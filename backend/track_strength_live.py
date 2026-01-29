"""
Live Strength Tracker - Real-time monitoring
Watches new signals as they come in and tracks their strength values
"""

import asyncio
import time
from datetime import datetime, timezone
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

class StrengthTracker:
    def __init__(self):
        self.last_timestamp = None
        self.signal_count = 0
        
    async def watch(self, duration_minutes=30):
        """
        Watch for new signals in real-time
        
        Args:
            duration_minutes: How long to monitor (default 30 min)
        """
        print("=" * 80)
        print("🔴 LIVE STRENGTH TRACKER - MONITORING MODE")
        print("=" * 80)
        print(f"Duration: {duration_minutes} minutes")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print(f"{'Time':<10} {'Dir':<5} {'Conf%':<7} {'Str%':<7} {'Price':<10} {'Notes':<30}")
        print("-" * 80)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        while time.time() < end_time:
            try:
                # Fetch latest entry
                res = db.client.table(settings.TABLE_ANALYSIS_LOG)\
                    .select("*")\
                    .order("timestamp", desc=True)\
                    .limit(1)\
                    .execute()
                
                if res.data:
                    entry = res.data[0]
                    ts = entry['timestamp']
                    
                    # Check if this is a new signal
                    if self.last_timestamp is None or ts != self.last_timestamp:
                        self.last_timestamp = ts
                        self.signal_count += 1
                        
                        # Extract data
                        time_str = datetime.fromisoformat(ts.replace('Z', '+00:00')).strftime('%H:%M:%S')
                        direction = entry['direction']
                        conf = entry['confidence']
                        strength = entry.get('strength', 0)
                        price = entry['price']
                        
                        # Categorize
                        if strength < 0.5:
                            note = "⚠️ LOW STRENGTH - Watch for fakeout"
                        elif strength < 0.7:
                            note = "📊 MEDIUM STRENGTH"
                        else:
                            note = "✅ HIGH STRENGTH - Good follow-through"
                        
                        # Print
                        print(f"{time_str:<10} {direction:<5} {conf*100:>5.1f}% {strength*100:>5.1f}% {price:<10.5f} {note:<30}")
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                await asyncio.sleep(10)
        
        print()
        print("=" * 80)
        print(f"📊 MONITORING COMPLETE")
        print(f"Total signals captured: {self.signal_count}")
        print("=" * 80)

async def main():
    tracker = StrengthTracker()
    await tracker.watch(duration_minutes=60)  # Monitor for 1 hour

if __name__ == "__main__":
    asyncio.run(main())
