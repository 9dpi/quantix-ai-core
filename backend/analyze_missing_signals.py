from quantix_core.database.connection import SupabaseConnection
from quantix_core.engine.confidence_refiner import ConfidenceRefiner
from datetime import datetime, timezone

# Recent high confidence logs
logs = [
    {'timestamp': '2026-02-10T06:08:01.819496+00:00', 'confidence': 0.72},
    {'timestamp': '2026-02-10T06:05:00.618371+00:00', 'confidence': 0.72},
    {'timestamp': '2026-02-10T06:01:59.257762+00:00', 'confidence': 0.75},
    {'timestamp': '2026-02-10T05:58:57.943324+00:00', 'confidence': 0.74},
    {'timestamp': '2026-02-10T05:55:56.709476+00:00', 'confidence': 0.73}
]

refiner = ConfidenceRefiner()

print(f"{'Time (UTC)':<10} | {'Raw':<5} | {'Release':<8} | {'Reason'}")
print("-" * 65)

for log in logs:
    ts_str = log['timestamp']
    raw_conf = log['confidence']
    
    # Parse timestamp manually to datetime object
    # Python 3.11 supports ISO format directly, but let's be safe with string slicing if needed
    try:
        dt = datetime.fromisoformat(ts_str)
    except:
         # Fallback manual parsing if isoformat doesn't like the +00:00
         dt = datetime.strptime(ts_str.split('.')[0], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)

    # We need to monkey-patch datetime.now() because calculate_release_score uses datetime.now() inside
    # Wait, calculate_release_score takes `df` and uses `datetime.now()` internally for hour check.
    # Refiner logic:
    #   s_weight = self.get_session_weight(now)
    #   now = datetime.now(...)
    
    # We can invoke get_session_weight directly for analysis!
    s_weight = refiner.get_session_weight(dt)
    
    # Assuming volatility and spread factor are 1.0 (default unless overridden)
    # Volatility factor is placeholder=1.0 in code
    # Spread factor is 0.5 only for rollover (21-23), else 1.0
    
    sp_factor = refiner.get_spread_factor("EURUSD") # This uses current time, so we need to mock it or rewrite logic
    # Actually, let's just calculate manually based on known logic:
    # 21-23h -> 0.5, else 1.0
    hour = dt.hour
    if 21 <= hour <= 23:
        sp_factor_sim = 0.5
    else:
        sp_factor_sim = 1.0
        
    v_factor_sim = 1.0 # Default
    
    release_score = min(1.0, raw_conf * s_weight * v_factor_sim * sp_factor_sim)
    
    print(f"{dt.strftime('%H:%M'):<10} | {raw_conf:<5} | {release_score:<8.4f} | Sess:{s_weight} x Vol:1.0 x Spr:{sp_factor_sim}")
