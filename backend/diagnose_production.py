
import asyncio
import os
import requests
import time
from datetime import datetime, timezone, timedelta
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

# ANSI Colors for checking via CLI (Logs will strip these usually, but good for realtime)
OK = "OK"
FAIL = "FAIL"
WARN = "WARNING"

async def check_database_flow():
    start = time.time()
    try:
        # 1. Check Connectivity
        res = db.client.table(settings.TABLE_SIGNALS).select("count", count="exact").limit(1).execute()
        latency_ms = (time.time() - start) * 1000
        
        # 2. Check for ZOMBIES (Waiting but no Telegram ID > 2 mins)
        zombie_limit = (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat()
        zombies = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .eq("state", "WAITING_FOR_ENTRY")\
            .is_("telegram_message_id", "null")\
            .lt("generated_at", zombie_limit)\
            .execute()
        zombie_count = len(zombies.data) if zombies.data else 0

        # 3. Check for STUCK ACTIVE TRADES (> 60 mins)
        stuck_limit = (datetime.now(timezone.utc) - timedelta(minutes=60)).isoformat()
        stuck = db.client.table(settings.TABLE_SIGNALS)\
            .select("id")\
            .eq("state", "ENTRY_HIT")\
            .lt("generated_at", stuck_limit)\
            .execute()
        stuck_count = len(stuck.data) if stuck.data else 0

        status = FAIL if latency_ms > 2000 else OK
        print(f"[{status}] Database Connect | Latency: {latency_ms:.2f}ms")
        
        if zombie_count > 0:
            print(f"[{FAIL}] ZOMBIE ALERT    | Found {zombie_count} signals stuck in WAITING without TG ID.")
        else:
            print(f"[{OK}] Pipe Cleanliness | No zombie signals found.")
            
        if stuck_count > 0:
            print(f"[{WARN}] STUCK TRADES    | Found {stuck_count} active trades running > 1 hour.")
        else:
            print(f"[{OK}] Trade Flow       | No stuck active trades.")
            
        return True
    except Exception as e:
        print(f"[{FAIL}] Database Error   | {e}")
        return False

def check_external_apis():
    # 1. Twelve Data
    start = time.time()
    try:
        api_key = settings.TWELVE_DATA_API_KEY
        url = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=15min&outputsize=1&apikey={api_key}"
        res = requests.get(url, timeout=5)
        latency = (time.time() - start) * 1000
        if res.status_code == 200 and res.json().get("status") == "ok":
            print(f"[{OK}] TwelveData API   | Latency: {latency:.2f}ms | Credits: OK")
        else:
            print(f"[{FAIL}] TwelveData API   | Error: {res.text}")
    except Exception as e:
        print(f"[{FAIL}] TwelveData API   | Connection Failed: {e}")

    # 2. Telegram
    start = time.time()
    try:
        res = requests.get(f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe", timeout=5)
        latency = (time.time() - start) * 1000
        if res.status_code == 200:
            print(f"[{OK}] Telegram API     | Latency: {latency:.2f}ms | Bot: Online")
        else:
            print(f"[{FAIL}] Telegram API     | Error: {res.status_code}")
    except Exception as e:
        print(f"[{FAIL}] Telegram API     | Connection Failed: {e}")

async def main():
    print(f"\nQUANTIX STREAM DIAGNOSTICS - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    await check_database_flow()
    print("-" * 60)
    check_external_apis()
    print("=" * 60)
    print("Diagnostics complete.\n")

if __name__ == "__main__":
    asyncio.run(main())
