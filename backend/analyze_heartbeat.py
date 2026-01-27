
import json
import os
from datetime import datetime, timezone
import statistics

def analyze_heartbeat():
    audit_file = os.path.join(os.path.dirname(__file__), 'heartbeat_audit.jsonl')
    output_file = os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'learning_data.json')
    
    if not os.path.exists(audit_file):
        print(f"❌ Audit file not found: {audit_file}")
        return

    history = []
    try:
        with open(audit_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("status") == "ANALYZED":
                            history.append(data)
                    except:
                        continue
    except Exception as e:
        print(f"❌ Error reading audit file: {e}")
        return

    if len(history) < 10:
        print("ℹ️ Not enough data to calculate performance.")
        return

    # 1. Basic Stats
    confidences = [h["confidence"] for h in history]
    avg_conf = statistics.mean(confidences)
    max_conf = max(confidences)
    
    # 2. Virtual Performance Simulation (Self-Learning)
    # Rules: If confidence > 0.70, simulate a BUY. 
    # Check outcome after 10 samples (approx 20 mins)
    wins = 0
    losses = 0
    total_trades = 0
    
    for i in range(len(history) - 10):
        point = history[i]
        if point["confidence"] >= 0.25:
            total_trades += 1
            entry_price = point["price"]
            # Look ahead 10 samples (approx 20-30 mins)
            future_price = history[i+10]["price"]
            
            if future_price > entry_price:
                wins += 1
            else:
                losses += 1

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
    
    # 3. Trend
    trend = "STABLE"
    if len(confidences) >= 5:
        last_5 = confidences[-5:]
        if last_5[-1] > last_5[0] + 0.05:
            trend = "RISING"
        elif last_5[-1] < last_5[0] - 0.05:
            trend = "FALLING"

    learning_telemetry = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(history),
        "avg_confidence": round(avg_conf, 4),
        "peak_confidence": round(max_conf, 4),
        "current_trend": trend,
        "performance": {
            "total_signals": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1)
        },
        "recent_history": [
            {"t": h["timestamp"], "v": round(h["confidence"] * 100, 1)} 
            for h in history[-24:]
        ]
    }

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(learning_telemetry, f, indent=2)
        print(f"✅ Performance learning updated: {total_trades} signals analyzed.")
    except Exception as e:
        print(f"❌ Failed to export: {e}")

if __name__ == "__main__":
    analyze_heartbeat()
