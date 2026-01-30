
import os
import requests
from dotenv import load_dotenv

def test_templates():
    load_dotenv("d:/Automator_Prj/Quantix_AI_Core/backend/.env")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Missing credentials")
        return

    # Mock Signal Data
    signal = {
        "asset": "EUR/USD",
        "timeframe": "M15",
        "direction": "SELL",
        "status": "ACTIVE",
        "ai_confidence": 0.97,
        "strength": 0.91,
        "entry_low": 1.19498,
        "tp": 1.19298,
        "sl": 1.19648,
        "validity": 90,
        "validity_passed": 12
    }

    # Format logic (simplified version of what's in the files)
    def format_msg(sig):
        confidence = int(sig['ai_confidence'] * 100)
        dir_emoji = "🔴" if sig['direction'] == "SELL" else "🟢"
        
        # ULTRA
        if confidence >= 95:
            return (
                f"🚨 *ULTRA SIGNAL (95%+)*\n\n"
                f"EURUSD | M15\n"
                f"{dir_emoji} {sig['direction']}\n\n"
                f"Status: 🟢 ACTIVE\n"
                f"Entry window: OPEN\n\n"
                f"Confidence: {confidence}%\n"
                f"Strength: {int(sig['strength']*100)}%\n\n"
                f"🎯 Entry: {sig['entry_low']}\n"
                f"💰 TP: {sig['tp']}\n"
                f"🛑 SL: {sig['sl']}\n"
            )
        return "Other Template"

    msg = format_msg(signal)
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        res = requests.post(url, json={
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown"
        }, timeout=10)
        
        if res.ok:
            print("✅ Template Test Message Sent Successfully!")
        else:
            print(f"❌ Failed: {res.text}")
    except Exception as e:
        print(f"🔥 Error: {e}")

if __name__ == "__main__":
    test_templates()
