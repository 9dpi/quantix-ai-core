
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Tìm đường dẫn tuyệt đối đến .env
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

token = os.getenv("TELEGRAM_BOT_TOKEN")
admin_chat_id = "7985984228"

def send_test():
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not found in .env")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    now_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    
    payload = {
        "chat_id": admin_chat_id,
        "text": f"🚀 *QUANTIX SYSTEM VERIFICATION*\n\n"
                f"📡 *Kênh:* Quản trị nội bộ (Admin)\n"
                f"✅ *Trạng thái:* Kết nối hoạt động tốt\n"
                f"⏱️ *Thời gian:* `{now_utc} UTC`\n\n"
                f"Tôi đã xác nhận các bản tin nội bộ và lệnh điều khiển sẽ được gửi qua ID này.",
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Success! Admin Message ID: {response.json().get('result', {}).get('message_id')}")
    except Exception as e:
        print(f"❌ Failed to reach admin: {e}")

if __name__ == "__main__":
    send_test()
