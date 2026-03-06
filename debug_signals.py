import os
import sys
from datetime import datetime, timezone
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from quantix_core.database.connection import db

def debug_signal_release():
    print("--- DEEP AUDIT: WHY SIGNALS WERE NOT RELEASED ---")
    try:
        res = db.client.table("fx_signals")\
            .select("generated_at, asset, direction, state, ai_confidence, release_confidence, telegram_message_id, refinement_reason")\
            .order("generated_at", desc=True)\
            .limit(10)\
            .execute()
        
        if not res.data:
            print("No signals found.")
            return

        for s in res.data:
            gen_at = s.get("generated_at", "N/A")
            asset = s.get("asset", "UNK")
            direction = s.get("direction", "???")
            state = s.get("state", "UNKNOWN")
            ai_conf = s.get("ai_confidence", 0)
            rel_conf = s.get("release_confidence", 0)
            tg_id = s.get("telegram_message_id")
            reason = s.get("refinement_reason", "NONE")
            
            status = "✅ SENT" if tg_id else "❌ NOT SENT"
            
            print(f"[{gen_at}] {asset:8} | {direction:4} | {state:15} | AI: {ai_conf*100:.0f}% | REL: {rel_conf*100:.0f}% | {status}")
            print(f"   Refinement: {reason}")
            if tg_id:
                print(f"   Telegram ID: {tg_id}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_signal_release()
