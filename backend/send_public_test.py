
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Tìm đường dẫn tuyệt đối đến .env
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

token = os.getenv("TELEGRAM_BOT_TOKEN")
public_chat_id = "-1003211826302"

def send_test_signal():
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    now_utc = datetime.utcnow()
    expiry_at = (now_utc + timedelta(minutes=15)).strftime('%H:%M UTC')
    
    message = (
        f"🚨 *NEW SIGNAL (TEST)*\n\n"
        f"Asset: EURUSD\n"
        f"Timeframe: M15\n"
        f"Direction: 🟢 BUY\n\n"
        f"Status: ⏳ WAITING FOR ENTRY\n"
        f"Entry Price: 1.08550\n"
        f"Take Profit: 1.08650\n"
        f"Stop Loss: 1.08450\n\n"
        f"Confidence: 92%\n"
        f"Valid Until: {expiry_at}\n\n"
        f"⚠️ Đây là bản tin thử nghiệm để xác minh kênh tín hiệu công khai."
    )
    
    payload = {
        "chat_id": public_chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Success! Public Signal ID: {response.json().get('result', {}).get('message_id')}")
    except Exception as e:
        print(f"❌ Failed to reach public channel: {e}")

if __name__ == "__main__":
    send_test_signal()
