
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")

def test_telegram():
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🛠️ Quantix Connection Test\nStatus: Testing Data Flow...",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Success! Message ID: {response.json().get('result', {}).get('message_id')}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_telegram()
