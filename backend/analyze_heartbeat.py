
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
                            history.append({
                                "timestamp": data["timestamp"],
                                "confidence": data["confidence"]
                            })
                    except:
                        continue
    except Exception as e:
        print(f"❌ Error reading audit file: {e}")
        return

    if not history:
        print("ℹ️ No analysis data found in log.")
        return

    # Statistics
    confidences = [h["confidence"] for h in history]
    avg_conf = statistics.mean(confidences)
    max_conf = max(confidences)
    recent = history[-24:] # Last 2 hours approx at 5m interval, or more at 2m
    
    # Trend calculation (last 5 points)
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
        "recent_history": [
            {"t": h["timestamp"], "v": round(h["confidence"] * 100, 1)} 
            for h in recent
        ]
    }

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(learning_telemetry, f, indent=2)
        print(f"✅ Learning data exported to {output_file}")
    except Exception as e:
        print(f"❌ Failed to export: {e}")

if __name__ == "__main__":
    analyze_heartbeat()
