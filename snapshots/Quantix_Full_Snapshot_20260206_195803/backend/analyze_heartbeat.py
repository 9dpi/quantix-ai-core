
import json
import os
import subprocess
from datetime import datetime, timezone
import statistics
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

def analyze_heartbeat(push_to_git=False):
    # Use absolute paths to prevent "reset to 0" issues on different CWDs
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audit_file = os.path.join(base_dir, 'backend', 'heartbeat_audit.jsonl')
    output_file = os.path.join(base_dir, 'dashboard', 'learning_data.json')
    
    history = []

    # 1. Primary Source: Supabase [T1] (Persistent / Cloud)
    try:
        if db.client:
            res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("*").order("timestamp", desc=False).execute()
            if res.data:
                history = res.data
                print(f"📊 Using Cloud Intelligence ({len(history)} samples from Supabase)")
    except Exception as e:
        print(f"⚠️ Supabase fetch failed, falling back to local: {e}")

    # 2. Secondary/Fallback Source: Local Log
    if not history:
        if os.path.exists(audit_file):
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
                if history:
                    print(f"📊 Using Local Intelligence ({len(history)} samples from log file)")
            except Exception as e:
                print(f"❌ Error reading local audit file: {e}")

    if len(history) < 2: 
        print("ℹ️ Not enough data to calculate performance.")
        return

    # 1. Basic Stats
    confidences = [h["confidence"] for h in history]
    avg_conf = statistics.mean(confidences)
    max_conf = max(confidences)
    
    # 2. Virtual Performance Simulation (Three-State Learning: BUY, SELL, HOLD)
    stats = {
        "BUY": {"total": 0, "wins": 0},
        "SELL": {"total": 0, "wins": 0},
        "HOLD": {"total": 0, "wins": 0}
    }
    
    threshold = 0.25 
    flat_threshold = 0.00010 
    
    # Calculate performance if we have enough samples to look ahead
    look_ahead = 10
    for i in range(len(history) - look_ahead):
        point = history[i]
        entry_price = point["price"]
        future_price = history[i+look_ahead]["price"]
        direction = point.get("direction", "BUY")
        
        if point["confidence"] >= threshold:
            if direction == "BUY":
                stats["BUY"]["total"] += 1
                if future_price > entry_price + 0.00005:
                    stats["BUY"]["wins"] += 1
            else: # SELL
                stats["SELL"]["total"] += 1
                if future_price < entry_price - 0.00005:
                    stats["SELL"]["wins"] += 1
        else:
            stats["HOLD"]["total"] += 1
            if abs(future_price - entry_price) <= flat_threshold:
                stats["HOLD"]["wins"] += 1

    total_trades = stats["BUY"]["total"] + stats["SELL"]["total"] + stats["HOLD"]["total"]
    total_wins = stats["BUY"]["wins"] + stats["SELL"]["wins"] + stats["HOLD"]["wins"]
    win_rate = (total_wins / total_trades * 100) if total_trades > 0 else 0
    
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
            "wins": total_wins,
            "win_rate": round(win_rate, 1),
            "details": stats
        },
        "recent_history": [
            {"t": h["timestamp"], "v": round(h["confidence"] * 100, 1)} 
            for h in history[-48:] 
        ]
    }

    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(learning_telemetry, f, indent=2)
        print(f"✅ Learning data updated ({len(history)} samples).")
        
        # Optional Auto-Push to GitHub to keep web dashboard synced
        if push_to_git:
            try:
                # Add learning data and the log itself for decentralization
                subprocess.run(["git", "add", "dashboard/learning_data.json", "backend/heartbeat_audit.jsonl"], cwd=base_dir, capture_output=True)
                subprocess.run(["git", "commit", "-m", "chore: auto-update learning telemetry"], cwd=base_dir, capture_output=True)
                subprocess.run(["git", "push"], cwd=base_dir, capture_output=True)
                print("🚀 Public Dashboard Sync Successful")
            except Exception as ge:
                print(f"⚠️ Git push failed: {ge}")
                
    except Exception as e:
        print(f"❌ Failed to export: {e}")

if __name__ == "__main__":
    analyze_heartbeat(push_to_git=False)
