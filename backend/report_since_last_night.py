
import asyncio
from quantix_core.database.connection import db
from datetime import datetime, timezone, timedelta

async def check_signals_since_last_night():
    # 18:00 VN yesterday = 11:00 UTC yesterday
    # Current time VN is 07:46, which is 00:46 UTC
    # 18:00 VN = UTC + 7 -> UTC = 11:00
    
    now_utc = datetime.now(timezone.utc)
    # Start time: Yesterday at 11:00 UTC
    start_time = (now_utc - timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0)
    
    print(f"--- BÁO CÁO TÍN HIỆU TỪ {start_time.isoformat()} UTC (18:00 VN hôm qua) ---")
    
    try:
        res = db.client.table('fx_signals').select('*').gte('generated_at', start_time.isoformat()).order('generated_at', desc=True).execute()
        
        if res.data:
            total = len(res.data)
            published = [s for s in res.data if s.get('status') == 'PUBLISHED' or s.get('telegram_message_id') is not None]
            detected = [s for s in res.data if s.get('status') == 'DETECTED' and s.get('telegram_message_id') is None]
            
            print(f"\nTổng số tín hiệu AI phát hiện: {total}")
            print(f"✅ Đã gửi Telegram: {len(published)}")
            print(f"🔍 Chỉ lưu nội bộ (Chờ lọc): {len(detected)}")
            
            print("\n--- Chi tiết tín hiệu đã gửi (PUBLISHED) ---")
            for s in published:
                print(f"🕒 {s.get('generated_at')} | {s.get('asset')} | {s.get('direction')} | Conf: {s.get('ai_confidence')} | Status: {s.get('status')} | TG_ID: {s.get('telegram_message_id')}")
                
            print("\n--- Chi tiết tín hiệu bị lọc (DETECTED) ---")
            for s in detected:
                # Get refinement reason if available
                reason = s.get('refinement_reason') or "Confidence < 0.75"
                print(f"🕒 {s.get('generated_at')} | {s.get('asset')} | {s.get('direction')} | Conf: {s.get('ai_confidence')} | {reason}")
        else:
            print("\nKhông tìm thấy tín hiệu nào trong khoảng thời gian này.")
            
    except Exception as e:
        print(f"Lỗi truy vấn: {e}")

if __name__ == "__main__":
    asyncio.run(check_signals_since_last_night())
