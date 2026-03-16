
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

supabase = create_client(url, key)

print("--- SIGNAL DELIVERY STATS (Today) ---")
try:
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    res = supabase.table("fx_signals").select("id, telegram_message_id").gte("generated_at", today).execute()
    signals = res.data or []
    
    total = len(signals)
    sent = sum(1 for s in signals if s.get("telegram_message_id") is not None)
    
    print(f"Total signals today: {total}")
    print(f"Signals with Telegram ID: {sent}")
    print(f"Signals MISSING Telegram ID: {total - sent}")
    
    if total - sent > 0:
        print("\nPossible reasons:")
        print("1. Telegram push failed (check logs for 'Telegram broadcast failed')")
        print("2. Release confidence threshold was met but TG notifier was missing (unlikely as health report works)")
        print("3. State update to DB after TG push failed (signal pushed but ID not saved)")

except Exception as e:
    print(f"Error: {e}")
