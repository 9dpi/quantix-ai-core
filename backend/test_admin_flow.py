
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_chat_id = "7985984228" # ID Admin theo yêu cầu

def test_admin_notification():
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": admin_chat_id,
        "text": "🤖 *QUANTIX INTERNAL TEST*\n\n"
                "🛡️ *Status:* Admin Data Flow Verified\n"
                "📡 *Mode:* Internal Feedback Enabled\n"
                "⏱️ *Time:* 2026-02-02 09:30 UTC\n\n"
                "Tất cả các bản tin nội bộ sẽ được gửi về kênh này.",
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"Success! Admin Message ID: {response.json().get('result', {}).get('message_id')}")
    except Exception as e:
        print(f"Failed to send to admin: {e}")

if __name__ == "__main__":
    test_admin_notification()
