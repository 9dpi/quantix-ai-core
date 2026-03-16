
import os
import requests
from dotenv import load_dotenv

load_dotenv('d:/Automator_Prj/Quantix_AI_Core/backend/.env')

token = os.environ.get("TELEGRAM_BOT_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
admin_id = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")

def test_send(cid, label):
    print(f"Testing {label} (ID: {cid})...")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": cid, "text": f"🚀 Diagnostic Test for {label}"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"Response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")

test_send(admin_id, "ADMIN")
test_send(chat_id, "SIGNAL_CHANNEL")
