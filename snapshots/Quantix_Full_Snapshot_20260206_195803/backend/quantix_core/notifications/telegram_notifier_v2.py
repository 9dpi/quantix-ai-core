"""
Telegram Notifier v2 - State-Based Message Templates

Sends Telegram notifications for each state transition in the signal lifecycle.
Each state has its own dedicated message template.
"""

import os
import json
import requests
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


class TelegramNotifierV2:
    """
    Sends state-specific Telegram messages for signal lifecycle events.
    
    Templates:
    - WAITING_FOR_ENTRY: Initial signal creation
    - ENTRY_HIT: Entry price touched
    - TP_HIT: Take profit reached
    - SL_HIT: Stop loss reached
    - CANCELLED: Signal expired without entry
    """
    
    def __init__(self, bot_token: str, chat_id: str, admin_chat_id: Optional[str] = None):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat/channel ID for signals
            admin_chat_id: Optional chat ID for system alerts
        """
        self.bot_token = str(bot_token).strip()
        self.chat_id = str(chat_id).strip()
        self.admin_chat_id = str(admin_chat_id).strip() if admin_chat_id else None
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        
        # Diagnostic Log
        safe_token = f"{self.bot_token[:5]}...{self.bot_token[-5:]}" if len(self.bot_token) > 10 else "INVALID"
        logger.info(f"TelegramNotifierV2 sanitized. Token: {safe_token}")
        
        # Memory set to track signals where ENTRY_HIT has been notified.
        self._notified_entries = set()
        
        # Initialize update tracker
        self._last_update_id = None
        self._startup_checked = False
        
        logger.info(f"TelegramNotifierV2 initialized (chat_id={chat_id}, admin={admin_chat_id})")
    
    def send_message(self, text: str) -> bool:
        """
        Send message to Telegram.
        
        Args:
            text: Message text (Markdown formatted)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("result", {}).get("message_id")
            
            logger.success(f"Telegram message sent successfully (ID: {message_id})")
            return message_id
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None
    
    # ========================================
    # STATE-SPECIFIC MESSAGE METHODS
    # ========================================
    
    def send_waiting_for_entry(self, signal: dict) -> Optional[int]:
        """
        Send WAITING_FOR_ENTRY message (State 1).
        
        Triggered when signal is first created.
        
        Args:
            signal: Signal dict with entry_price, tp, sl, confidence, expiry_at
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        tp = signal.get("tp", 0)
        sl = signal.get("sl", 0)
        confidence = int(signal.get("release_confidence", signal.get("ai_confidence", 0)) * 100)
        
        # Format expiry time
        expiry_str = self._format_expiry_time(signal.get("expiry_at"))
        
        # Direction emoji
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        message = (
            f"{test_tag}🚨 *NEW SIGNAL*\n\n"
            f"Asset: {asset}\n"
            f"Timeframe: {timeframe}\n"
            f"Direction: {dir_emoji} {direction}\n\n"
            f"Status: ⏳ WAITING FOR ENTRY\n"
            f"Entry Price: {entry}\n"
            f"Take Profit: {tp}\n"
            f"Stop Loss: {sl}\n\n"
            f"Confidence: {confidence}%\n"
            f"Valid Until: {expiry_str}\n\n"
            f"⏱ *Entry valid:* 15 minutes\n"
            f"⏱ *Max trade duration:* 35 minutes\n\n"
            f"⚠️ Signal will auto-expire if entry is not reached within 15m."
        )
        
        logger.info(f"Sending WAITING_FOR_ENTRY message for {asset}")
        return self.send_message(message)
    
    def send_entry_hit(self, signal: dict) -> Optional[int]:
        """
        Send ENTRY_HIT message (State 2).
        
        Triggered when price touches entry level.
        
        Args:
            signal: Signal dict with asset, timeframe, direction, entry_price
        """
        signal_id = signal.get("id")
        self._notified_entries.add(signal_id)
        
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        message = (
            f"{test_tag}📍 *ENTRY PRICE HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"Time: {datetime.utcnow().strftime('%H:%M UTC')}\n\n"
            f"Status: 🔵 ENTRY CONFIRMED\n\n"
            f"🎯 TP: {signal.get('tp')}\n"
            f"🛑 SL: {signal.get('sl')}\n\n"
            f"Trade is now ACTIVE.\n"
            f"Waiting for TP or SL."
        )
        
        logger.info(f"Sending ENTRY_HIT message for {asset}")
        
        # If we have a telegram_message_id, reply to it
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)
    
    def send_tp_hit(self, signal: dict) -> Optional[int]:
        """
        Send TP_HIT message (State 3a).
        
        Triggered when price touches take profit.
        
        Args:
            signal: Signal dict with asset, timeframe, direction, entry_price
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        # Rule: BLOCK if ENTRY_HIT was not sent by this instance
        signal_id = signal.get("id")
        if signal_id not in self._notified_entries:
            logger.warning(f"⛔ Blocked TP_HIT for {signal_id} (Orphan: Entry not notified)")
            return None
        
        message = (
            f"{test_tag}✅ *TAKE PROFIT HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"TP: {signal.get('tp')}\n\n"
            f"Status: 🏁 CLOSED_TP\n"
            f"Result: 🟢 PROFIT\n"
            f"R:R: 1 : 1\n\n"
            f"Signal lifecycle completed."
        )
        
        logger.info(f"Sending TP_HIT message for {asset}")
        
        # If we have a telegram_message_id, reply to it
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)
    
    def send_sl_hit(self, signal: dict) -> Optional[int]:
        """
        Send SL_HIT message (State 3b).
        
        Triggered when price touches stop loss.
        
        Args:
            signal: Signal dict with asset, timeframe, direction, entry_price
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        # Rule: BLOCK if ENTRY_HIT was not sent by this instance
        signal_id = signal.get("id")
        if signal_id not in self._notified_entries:
            logger.warning(f"⛔ Blocked SL_HIT for {signal_id} (Orphan: Entry not notified)")
            return None
        
        message = (
            f"{test_tag}🛑 *STOP LOSS HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"SL: {signal.get('sl')}\n\n"
            f"Status: 🏁 CLOSED_SL\n"
            f"Result: 🔴 LOSS\n\n"
            f"Signal lifecycle completed."
        )
        
        logger.info(f"Sending SL_HIT message for {asset}")
        
        # If we have a telegram_message_id, reply to it
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)
    
    def send_time_exit(self, signal: dict, current_price: float) -> Optional[int]:
        """
        Send TIME_EXIT message (State 3c).
        
        Triggered when a trade is closed due to max duration limit.
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        # Calculate result
        diff = float(current_price) - float(entry)
        if direction == "SELL":
            diff = -diff
        
        result_icon = "🔵"
        result_text = "BREAKEVEN / NEUTRAL"
        if diff > 0.00001: # Small epsilon for pips
            result_icon = "🟢"
            result_text = "PROFIT (Time Exit)"
        elif diff < -0.00001:
            result_icon = "🔴"
            result_text = "LOSS (Time Exit)"

        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        message = (
            f"{test_tag}⏱️ *CLOSED (Timeout)*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"Exit (Market): {current_price}\n\n"
            f"Status: 🏁 CLOSED_TIMEOUT\n"
            f"Result: {result_icon} {result_text}\n"
            f"Reason: Trade exceeded max duration (35m)\n\n"
            f"System released for new signals."
        )
        
        logger.info(f"Sending TIME_EXIT message for {asset}")
        
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)
    
    def send_cancelled(self, signal: dict) -> Optional[int]:
        """
        Send CANCELLED message (State 4).
        
        Triggered when signal expires without entry being touched.
        
        Args:
            signal: Signal dict with asset, timeframe
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        message = (
            f"{test_tag}⚪ *EXPIRED*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Status: 🏁 EXPIRED\n"
            f"Result: ⚪ NOT_TRIGGERED\n"
            f"Reason: Entry price was not reached within 15m.\n\n"
            f"Signal removed from watchlist."
        )
        
        logger.info(f"Sending CANCELLED message for {asset}")
        
        # If we have a telegram_message_id, reply to it
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)

    def reply_to_message(self, message_id: int, text: str) -> Optional[int]:
        """Send message as a reply to an existing message."""
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "reply_to_message_id": message_id,
                "parse_mode": "Markdown"
            }
            # Use params for consistency with _send_to_chat if needed, 
            # but sendMessage POST with json is standard.
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            new_msg_id = data.get("result", {}).get("message_id")
            logger.info(f"✅ Reply sent to {message_id} (New ID: {new_msg_id})")
            return new_msg_id
        except Exception as e:
            logger.error(f"❌ Reply failed: {e}")
            return None

    def send_admin_notification(self, text: str) -> bool:
        """Send a general notification to the Admin chat (non-critical)."""
        if not self.admin_chat_id:
            return False
        return self._send_to_chat(self.admin_chat_id, text, use_markdown=True)

    def send_critical_alert(self, error_msg: str) -> bool:
        """Send a critical system alert (e.g. API Blocked) to Admin chat."""
        import os
        instance = os.getenv("INSTANCE_NAME", "UNKNOWN")
        target_chat = self.admin_chat_id or self.chat_id
        message = (
            f"🚨 *CRITICAL SYSTEM ALERT*\n\n"
            f"Instance: `{instance}`\n"
            f"Status: 🔴 SYSTEM STALLED\n\n"
            f"Error: `{error_msg}`\n\n"
            f"Action Required: Check Railway logs or API quota immediately."
        )
        return self._send_to_chat(target_chat, message)

    def _send_to_chat(self, chat_id: str, text: str, use_markdown: bool = False) -> bool:
        """Internal helper using URL parameters for maximum compatibility."""
        try:
            target_id = str(chat_id).strip()
            payload = {
                "chat_id": target_id,
                "text": text
            }
            if use_markdown:
                payload["parse_mode"] = "Markdown"
                
            # Use params= (URL encoded) instead of json= to match the successful curl test
            response = requests.post(self.api_url, params=payload, timeout=12)
            
            if response.status_code != 200:
                logger.error(f"❌ Telegram API Error ({response.status_code}): {response.text}")
                return False
                
            logger.info(f"✅ Reply successfully delivered to {target_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Network error: {e}")
            return False

    def get_updates(self, offset: Optional[int] = None) -> list:
        """Get latest updates from Telegram API."""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {"timeout": 20, "offset": offset}
            response = requests.get(url, params=params, timeout=25)
            response.raise_for_status()
            return response.json().get("result", [])
        except Exception as e:
            logger.error(f"⚠️ getUpdates failed: {e}")
            return []

    def handle_commands(self, watcher_instance=None):
        """Poll for commands and respond if from Admin."""
        if not self.admin_chat_id:
            return

        updates = self.get_updates(offset=getattr(self, '_last_update_id', None))
        if updates:
            logger.info(f"💾 Found {len(updates)} new Telegram updates")
            
        for update in updates:
            self._last_update_id = update['update_id'] + 1
            
            message = update.get("message")
            if not message or "text" not in message: continue
            
            # Security: Robust Chat ID comparison with EXPLICIT LOGGING
            current_chat_id = str(message['chat']['id']).strip()
            target_admin_id = str(self.admin_chat_id).strip()
            
            logger.debug(f"🔍 Comparing IDs: Sender={current_chat_id} | Admin={target_admin_id}")
            
            if current_chat_id != target_admin_id:
                logger.warning(f"🚫 Unauthorized ID {current_chat_id} tried: {message.get('text')}")
                continue

            text = message.get("text", "").strip()
            logger.success(f"📩 ADMIN COMMAND MATCHED: {text}")
            
            if text.startswith("/"):
                logger.info(f"⚡ Processing command: {text}")
                self._process_command(text, current_chat_id, watcher_instance)

    def _process_command(self, command: str, target_chat_id: str, watcher=None):
        """Internal command processor that replies directly to sender."""
        try:
            cmd = command.lower().split()[0]
            instance = os.getenv("INSTANCE_NAME", "RAILWAY-BOT")

            if cmd == "/help" or cmd == "/start":
                help_text = (
                    "🤖 QUANTIX ADMIN PANEL\n\n"
                    "📌 CÁC LỆNH ĐIỀU KHIỂN:\n"
                    "• /status - Kiểm tra sức khỏe & Stats\n"
                    "• /log - Chẩn đoán hệ thống chi tiết\n"
                    "• /unblock - GIẢI PHÓNG HỆ THỐNG (Khẩn cấp)\n"
                    "• /ping - Kiểm tra kết nối\n"
                    "• /signals - Số lượng tín hiệu đang canh\n"
                    "• /help - Hiện lại menu này\n\n"
                    f"Instance: {instance}\n"
                    "Status: Online 🟢"
                )
                self._send_to_chat(target_chat_id, help_text, use_markdown=False)

            elif cmd == "/ping":
                self._send_to_chat(target_chat_id, f"🏓 PONG!\n\nTôi đang lắng nghe bạn tại {instance} 🟢", use_markdown=False)

            elif cmd == "/status":
                # Fetch detailed metrics from database and watcher state
                try:
                    from quantix_core.database.connection import db
                    from quantix_core.config.settings import settings
                    
                    # 1. Today's Activity Breakdown
                    today = datetime.now(timezone.utc).date().isoformat()
                    
                    # Count Analysis Cycles (Market Scans)
                    scan_res = db.client.table(settings.TABLE_ANALYSIS_LOG).select("timestamp", count="exact").gte("timestamp", today).execute()
                    scan_count = scan_res.count if scan_res else 0
                    
                    # Count Signals Found (Candidates or Active)
                    found_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").gte("generated_at", today).execute()
                    found_count = found_res.count if found_res else 0
                    
                    # Count actual pushes to Telegram today (Status ACTIVE with TG ID)
                    push_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").gte("generated_at", today).not_.is_("telegram_message_id", "null").execute()
                    push_count = push_res.count if push_res else 0
                    
                    # 2. Watcher Stats
                    active_count = getattr(watcher, 'last_watched_count', 0) if watcher else 0
                    
                    # 3. Overall Performance
                    total_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").execute()
                    total_sigs = total_res.count if total_res else 0
                    
                    wins_res = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").eq("state", "TP_HIT").execute()
                    wins = wins_res.count if wins_res else 0

                    analyzer_status = "ACTIVE 🟢" if watcher else "STANDBY 🟡"

                    status_text = (
                        "📊 *QUANTIX LIVE STATUS*\n\n"
                        f"🖥️ *Instance:* `{instance}`\n"
                        f"📡 *Analyzer:* {analyzer_status}\n"
                        f"🕒 *UTC Time:* `{datetime.now(timezone.utc).strftime('%H:%M:%S')}`\n\n"
                        "🔍 *Today's Miner Activity:*\n"
                        f"• Market Scans: `{scan_count}` cycles\n"
                        f"• Potential Setups: `{found_count}` found\n"
                        f"• Telegram Pushes: `{push_count}` signals\n\n"
                        "🚀 *Watcher & Performance:*\n"
                        f"• Active Monitoring: `{active_count}` pairs\n"
                        f"• Total Signals (All-time): `{total_sigs}`\n"
                        f"• Total Wins (TP): `{wins}` trades\n\n"
                        "✅ *System Health:* All data flows operational."
                    )
                except Exception as db_err:
                    logger.error(f"Status DB query failed: {db_err}")
                    status_text = f"📊 *STATUS (LITE)*\n\nInstance: `{instance}`\nWatching: `{getattr(watcher, 'last_watched_count', 0)}` signals.\nError: Semi-connected to DB."

                self._send_to_chat(target_chat_id, status_text, use_markdown=True)

            elif cmd == "/signal" or cmd == "/signals":
                count = getattr(watcher, 'last_watched_count', 0) if watcher else 0
                self._send_to_chat(target_chat_id, f"🔍 TRA CỨU: Hệ thống đang canh chừng {count} cặp tiền. Mọi thứ đều ổn định.", use_markdown=False)
            
            elif cmd == "/log" or cmd == "/diag":
                try:
                    from quantix_core.database.connection import db
                    from quantix_core.config.settings import settings
                    from quantix_core.utils.market_hours import MarketHours
                    import time

                    # 1. DB Connectivity
                    db_ok = "✅" if db.health_check() else "❌"
                    
                    # 2. External APIs
                    td_ok = "❌"
                    try:
                        url = f"https://api.twelvedata.com/time_series?symbol=EUR/USD&interval=1min&outputsize=1&apikey={settings.TWELVE_DATA_API_KEY}"
                        res = requests.get(url, timeout=5)
                        if res.status_code == 200 and res.json().get("status") == "ok":
                            td_ok = "✅"
                    except: td_ok = "❌"

                    # 3. Market Status
                    mkt_ok = "🟢 OPEN" if MarketHours.is_market_open() else "🔴 CLOSED"

                    # 4. Invariants (Check for stuck signals)
                    from datetime import timedelta
                    stuck_pending_limit = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
                    stuck_pending = db.client.table(settings.TABLE_SIGNALS).select("id", count="exact").eq("state", "WAITING_FOR_ENTRY").lt("generated_at", stuck_pending_limit).execute()
                    stuck_count = stuck_pending.count if stuck_pending else 0
                    invariant_ok = "✅ CLEAN" if stuck_count == 0 else f"⚠️ {stuck_count} STUCK"

                    # 5. Heartbeat Status
                    last_log = db.client.table(settings.TABLE_ANALYSIS_LOG).select("timestamp").order("timestamp", desc=True).limit(1).execute()
                    hb_ok = "❌ STALE"
                    if last_log.data:
                        last_ts = datetime.fromisoformat(last_log.data[0]['timestamp'].replace('Z', '+00:00'))
                        if (datetime.now(timezone.utc) - last_ts).total_seconds() < 600:
                            hb_ok = "✅ ACTIVE"

                    log_text = (
                        "📋 *QUANTIX SYSTEM DIAGNOSTICS*\n"
                        "----------------------------------\n"
                        f"🗄️ *Database:* {db_ok}\n"
                        f"🌐 *Market Status:* {mkt_ok}\n"
                        f"📊 *Analyzer Heartbeat:* {hb_ok}\n"
                        f"🔑 *TwelveData API:* {td_ok}\n"
                        f"🛡️ *Invariant Check:* {invariant_ok}\n"
                        "----------------------------------\n"
                        f"⏱️ *Diagnostic Time:* `{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC`\n"
                        f"🖥️ *Instance:* `{instance}`"
                    )
                    self._send_to_chat(target_chat_id, log_text, use_markdown=True)
                except Exception as log_err:
                    logger.error(f"Diag command failed: {log_err}")
                    self._send_to_chat(target_chat_id, f"❌ Diagnostic failed: {log_err}", use_markdown=False)

            elif cmd == "/unblock" or cmd == "/clear":
                try:
                    from quantix_core.database.connection import db
                    from quantix_core.config.settings import settings
                    from datetime import timedelta
                    
                    self._send_to_chat(target_chat_id, "⚙️ Đang quét và giải phóng hệ thống...", use_markdown=False)
                    
                    # 1. Clear Stuck Pending (WAITING > 30m)
                    limit_30 = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
                    res_p = db.client.table(settings.TABLE_SIGNALS).update({
                        "state": "CANCELLED", "status": "EXPIRED", "result": "CANCELLED", "closed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("state", "WAITING_FOR_ENTRY").lt("generated_at", limit_30).execute()
                    count_p = len(res_p.data) if res_p.data else 0
                    
                    # 2. Clear Stuck Active (ENTRY_HIT > 90m)
                    limit_90 = (datetime.now(timezone.utc) - timedelta(minutes=90)).isoformat()
                    res_a = db.client.table(settings.TABLE_SIGNALS).update({
                        "state": "TIME_EXIT", "status": "CLOSED_TIMEOUT", "result": "CANCELLED", "closed_at": datetime.now(timezone.utc).isoformat()
                    }).eq("state", "ENTRY_HIT").lt("generated_at", limit_90).execute()
                    count_a = len(res_a.data) if res_a.data else 0
                    
                    total = count_p + count_a
                    if total > 0:
                        report = (
                            f"✅ *HỆ THỐNG ĐÃ ĐƯỢC GIẢI PHÓNG*\n\n"
                            f"• Đã đóng {count_p} lệnh chờ quá hạn (30m)\n"
                            f"• Đã đóng {count_a} lệnh chạy quá hạn (90m)\n\n"
                            f"🚀 Tổng cộng: `{total}` vật cản đã được dọn dẹp.\n"
                            f"Máy chủ `{instance}` đã sẵn sàng bắn tín hiệu mới."
                        )
                    else:
                        report = "ℹ️ *THÔNG BÁO*\n\nHệ thống hiện tại sạch sẽ, không có tín hiệu nào bị kẹt. Không cần xử lý."
                        
                    self._send_to_chat(target_chat_id, report, use_markdown=True)
                except Exception as unblock_err:
                    logger.error(f"Unblock command failed: {unblock_err}")
                    self._send_to_chat(target_chat_id, f"❌ Lỗi giải phóng: {unblock_err}", use_markdown=False)

            else:
                self._send_to_chat(target_chat_id, f"❓ Lệnh không hợp lệ: {cmd}. Gõ /help để xem danh sách.", use_markdown=False)
                logger.info(f"Unknown command: {cmd}")

        except Exception as e:
            logger.error(f"Error processing {command}: {e}")

    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _format_expiry_time(self, expiry_at: Optional[str]) -> str:
        """
        Format expiry timestamp as "HH:MM UTC".
        
        Args:
            expiry_at: ISO format timestamp string
        
        Returns:
            Formatted time string (e.g. "15:45 UTC")
        """
        if not expiry_at:
            return "N/A"
        
        try:
            # Parse ISO format (handle both Z and +00:00)
            dt = datetime.fromisoformat(expiry_at.replace("Z", "+00:00"))
            return dt.strftime("%H:%M UTC")
        except Exception as e:
            logger.warning(f"Failed to parse expiry time: {e}")
            return "N/A"


# ========================================
# CONVENIENCE FUNCTIONS
# ========================================

def create_notifier(bot_token: str, chat_id: str, admin_chat_id: Optional[str] = None) -> TelegramNotifierV2:
    """
    Create a TelegramNotifierV2 instance.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat/channel ID
        admin_chat_id: Optional admin chat ID
    
    Returns:
        TelegramNotifierV2 instance
    """
    return TelegramNotifierV2(bot_token, chat_id, admin_chat_id)
