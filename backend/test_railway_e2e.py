"""
RAILWAY E2E VALIDATION SCRIPT
Check if the cloud instance is healthy before cutover.
"""
import os
import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

def run_e2e_check():
    instance = os.getenv("INSTANCE_NAME", "RAILWAY-TEST")
    logger.info(f"🚀 Starting E2E Check for Instance: {instance}")
    
    # 1. Check Env Vars
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY", "TELEGRAM_BOT_TOKEN", "TWELVE_DATA_API_KEY"]
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"❌ Missing Env Var: {var}")
            return False
    logger.success("✅ Environment variables validated")

    # 2. Check Supabase Connectivity
    try:
        url = f"{os.getenv('SUPABASE_URL')}/rest/v1/fx_signals?select=id&limit=1"
        headers = {
            "apikey": os.getenv("SUPABASE_KEY"),
            "Authorization": f"Bearer {os.getenv('SUPABASE_KEY')}"
        }
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        logger.success("✅ Supabase connectivity OK")
    except Exception as e:
        logger.error(f"❌ Supabase failed: {e}")
        return False

    # 3. Check Telegram
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        text = f"🧪 *E2E TEST FROM {instance}*\nSystem is healthy and ready for parallel run."
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        res = requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        res.raise_for_status()
        logger.success("✅ Telegram test message sent")
    except Exception as e:
        logger.error(f"❌ Telegram failed: {e}")
        return False

    logger.info("======================================================")
    logger.success("🏆 RAILWAY E2E SUCCESSFUL!")
    logger.info("======================================================")
    return True

if __name__ == "__main__":
    run_e2e_check()
