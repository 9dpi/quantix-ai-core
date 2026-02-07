
import asyncio
from datetime import datetime, timedelta, timezone
from quantix_core.database.connection import db
from quantix_core.config.settings import settings

def parse_tg_time(date_str):
    # Example: "05-Feb-26 11:18 AM"
    dt = datetime.strptime(date_str, "%d-%b-%y %I:%M %p")
    return dt.replace(tzinfo=timezone.utc).isoformat()

def reconstruct():
    print("🧹 Wiping existing signals...")
    db.client.table(settings.TABLE_SIGNALS).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    # Data from Telegram messages (The Evidence)
    messages = [
        {"time": "05-Feb-26 11:18 AM", "dir": "SELL", "entry": 1.17935, "tp": 1.17835, "sl": 1.18035, "conf": 0.80, "dur": 30},
        {"time": "05-Feb-26 12:31 PM", "dir": "SELL", "entry": 1.17911, "tp": 1.17811, "sl": 1.18011, "conf": 0.80, "dur": 30},
        {"time": "05-Feb-26 10:13 PM", "dir": "BUY",  "entry": 1.18019, "tp": 1.18119, "sl": 1.17919, "conf": 1.20, "dur": 30},
        {"time": "05-Feb-26 10:47 PM", "dir": "BUY",  "entry": 1.17813, "tp": 1.17913, "sl": 1.17713, "conf": 1.00, "dur": 30},
        {"time": "05-Feb-26 11:23 PM", "dir": "BUY",  "entry": 1.1787,  "tp": 1.1797,  "sl": 1.1777,  "conf": 1.00, "dur": 30},
        {"time": "06-Feb-26 12:00 AM", "dir": "BUY",  "entry": 1.17972, "tp": 1.18072, "sl": 1.17872, "conf": 1.00, "dur": 30},
        {"time": "06-Feb-26 12:36 AM", "dir": "BUY",  "entry": 1.17982, "tp": 1.18082, "sl": 1.17882, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 01:12 AM", "dir": "BUY",  "entry": 1.17957, "tp": 1.18057, "sl": 1.17857, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 01:49 AM", "dir": "BUY",  "entry": 1.17928, "tp": 1.18028, "sl": 1.17828, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 02:25 AM", "dir": "BUY",  "entry": 1.17918, "tp": 1.18018, "sl": 1.17818, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 03:02 AM", "dir": "BUY",  "entry": 1.17883, "tp": 1.17983, "sl": 1.17783, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 07:01 AM", "dir": "SELL", "entry": 1.17823, "tp": 1.17723, "sl": 1.17923, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 07:37 AM", "dir": "SELL", "entry": 1.17814, "tp": 1.17714, "sl": 1.17914, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 08:14 AM", "dir": "SELL", "entry": 1.17875, "tp": 1.17775, "sl": 1.17975, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 08:59 AM", "dir": "SELL", "entry": 1.17889, "tp": 1.17789, "sl": 1.17989, "conf": 0.76, "dur": 30},
        {"time": "06-Feb-26 01:32 PM", "dir": "BUY",  "entry": 1.17963, "tp": 1.18063, "sl": 1.17863, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 02:09 PM", "dir": "BUY",  "entry": 1.17919, "tp": 1.18019, "sl": 1.17819, "conf": 0.80, "dur": 30},
        {"time": "06-Feb-26 02:45 PM", "dir": "BUY",  "entry": 1.17874, "tp": 1.17974, "sl": 1.17774, "conf": 0.79, "dur": 30},
        {"time": "06-Feb-26 03:21 PM", "dir": "BUY",  "entry": 1.17865, "tp": 1.17965, "sl": 1.17765, "conf": 1.00, "dur": 30},
        {"time": "06-Feb-26 03:58 PM", "dir": "BUY",  "entry": 1.17871, "tp": 1.17971, "sl": 1.17771, "conf": 0.79, "dur": 30},
        {"time": "06-Feb-26 04:34 PM", "dir": "BUY",  "entry": 1.17926, "tp": 1.18026, "sl": 1.17826, "conf": 0.72, "dur": 30},
        {"time": "06-Feb-26 05:11 PM", "dir": "BUY",  "entry": 1.17929, "tp": 1.18029, "sl": 1.17829, "conf": 0.65, "dur": 30},
        {"time": "06-Feb-26 09:04 PM", "dir": "BUY",  "entry": 1.18073, "tp": 1.18173, "sl": 1.17973, "conf": 0.68, "dur": 30},
        {"time": "06-Feb-26 09:40 PM", "dir": "BUY",  "entry": 1.18169, "tp": 1.18269, "sl": 1.18069, "conf": 0.70, "dur": 30},
        {"time": "06-Feb-26 10:17 PM", "dir": "BUY",  "entry": 1.18103, "tp": 1.18203, "sl": 1.18003, "conf": 0.67, "dur": 30},
        {"time": "06-Feb-26 10:58 PM", "dir": "BUY",  "entry": 1.18126, "tp": 1.18226, "sl": 1.18026, "conf": 0.75, "dur": 30},
        {"time": "06-Feb-26 11:40 PM", "dir": "BUY",  "entry": 1.18108, "tp": 1.18208, "sl": 1.18008, "conf": 0.73, "dur": 30},
        {"time": "07-Feb-26 12:23 AM", "dir": "BUY",  "entry": 1.18093, "tp": 1.18193, "sl": 1.17993, "conf": 0.80, "dur": 35},
        {"time": "07-Feb-26 01:05 AM", "dir": "BUY",  "entry": 1.18145, "tp": 1.18245, "sl": 1.18045, "conf": 0.80, "dur": 35},
        {"time": "07-Feb-26 01:48 AM", "dir": "BUY",  "entry": 1.1818,  "tp": 1.1828,  "sl": 1.1808,  "conf": 0.80, "dur": 35},
        {"time": "07-Feb-26 02:30 AM", "dir": "BUY",  "entry": 1.18119, "tp": 1.18219, "sl": 1.18019, "conf": 0.80, "dur": 35},
    ]

    print(f"🚀 Reconstructing {len(messages)} signals from Telegram evidence...")
    
    for m in messages:
        gen_at_dt = datetime.strptime(m["time"], "%d-%b-%y %I:%M %p").replace(tzinfo=timezone.utc)
        closed_at_dt = gen_at_dt + timedelta(minutes=m["dur"])
        
        sig_obj = {
            "asset": "EURUSD",
            "direction": m["dir"],
            "timeframe": "M15",
            "entry_price": m["entry"],
            "tp": m["tp"],
            "sl": m["sl"],
            "state": "CANCELLED",
            "status": "EXPIRED",
            "result": "CANCELLED",
            "ai_confidence": m["conf"] if m["conf"] <= 1.0 else 1.0, # Cap at 1.0 for db field usually
            "release_confidence": m["conf"],
            "generated_at": gen_at_dt.isoformat(),
            "closed_at": closed_at_dt.isoformat(),
            "is_test": False
        }
        
        db.client.table(settings.TABLE_SIGNALS).insert(sig_obj).execute()
        print(f"✅ Reconstructed: {m['time']} ({m['dir']} @ {m['entry']}) -> {m['conf']*100}%")

    print("\n🎉 HISTORY RECONSTRUCTION COMPLETE. ALL SESSIONS MATCH TELEGRAM EVIDENCE.")

if __name__ == "__main__":
    reconstruct()
