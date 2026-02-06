"""
Telegram Notifier v2 - State-Based Message Templates

Sends Telegram notifications for each state transition in the signal lifecycle.
Each state has its own dedicated message template.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
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
            f"⏱ *Entry valid:* 35 minutes\n"
            f"⏱ *Max trade duration:* 35 minutes\n\n"
            f"⚠️ Signal will auto-expire if entry is not reached within 35m."
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
        Send TIME_EXIT message (State 5).
        
        Triggered when an active signal exceeds its maximum duration.
        
        Args:
            signal: Signal dict with entry_price, tp, sl, confidence, expiry_at
            current_price: The current market price at the time of exit.
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        
        # Direction emoji
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        # Calculate result (profit/loss)
        result_text = "N/A"
        result_icon = "⚪"
        
        if direction == "BUY":
            if current_price > entry:
                result_text = "PROFIT"
                result_icon = "✅"
            elif current_price < entry:
                result_text = "LOSS"
                result_icon = "❌"
            else:
                result_text = "BREAKEVEN"
                result_icon = "➖"
        elif direction == "SELL":
            if current_price < entry:
                result_text = "PROFIT"
                result_icon = "✅"
            elif current_price > entry:
                result_text = "LOSS"
                result_icon = "❌"
            else:
                result_text = "BREAKEVEN"
                result_icon = "➖"
        
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
        Send CANCELLED message (State 6).
        
        Triggered when a signal expires without the entry price being hit.
        
        Args:
            signal: Signal dict with entry_price, tp, sl, confidence, expiry_at
        """
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        
        # Direction emoji
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        test_tag = "[TEST] " if signal.get("is_test") else ""
        
        message = (
            f"{test_tag}⚪ *EXPIRED*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Status: 🏁 EXPIRED\n"
            f"Result: ⚪ NOT_TRIGGERED\n"
            f"Reason: Entry price was not reached within 35m.\n\n"
            f"Signal removed from watchlist."
        )
        
        logger.info(f"Sending CANCELLED message for {asset}")
        
        # If we have a telegram_message_id, reply to it
        msg_id = signal.get("telegram_message_id")
        if msg_id:
            return self.reply_to_message(msg_id, message)
            
        return self.send_message(message)

    def _send_to_chat(self, chat_id: str, text: str, use_markdown: bool = True) -> Optional[int]:
        """
        Internal method to send a message to a specific chat ID.
        """
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown" if use_markdown else None
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            message_id = data.get("result", {}).get("message_id")
            
            logger.success(f"Admin message sent successfully to {chat_id} (ID: {message_id})")
            return message_id
        
        except Exception as e:
            logger.error(f"Failed to send admin Telegram message to {chat_id}: {e}")
            return None

    def _process_admin_command(self, message: dict):
        """
        Process admin commands received via Telegram.
        """
        text = message.get("text", "")
        chat_id = message["chat"]["id"]
        
        if not self.admin_chat_id or str(chat_id) != self.admin_chat_id:
            logger.warning(f"Unauthorized admin command from chat ID: {chat_id}")
            self._send_to_chat(chat_id, "🚫 *Unauthorized access.*", use_markdown=True)
            return
        
        logger.info(f"Admin command received: {text} from {chat_id}")
        
        parts = text.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        target_chat_id = self.admin_chat_id # Default to admin chat for responses
        
        if cmd == "/status":
            self._send_to_chat(target_chat_id, "✅ *Bot is running.*\n\n"
                                                f"Chat ID: `{self.chat_id}`\n"
                                                f"Admin Chat ID: `{self.admin_chat_id}`", use_markdown=True)
        elif cmd == "/echo":
            self._send_to_chat(target_chat_id, f"Echo: `{args}`", use_markdown=True)
        elif cmd == "/unblock" or cmd == "/clear":
            try:
                from quantix_core.database.connection import db
                from quantix_core.config.settings import settings
                
                self._send_to_chat(target_chat_id, "⚙️ Đang quét và giải phóng hệ thống...", use_markdown=False)
                
                # 1. Clear Stuck Pending (WAITING > 35m)
                limit_30 = (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat()
                res_p = db.client.table(settings.TABLE_SIGNALS).update({
                    "state": "CANCELLED", "status": "EXPIRED", "result": "CANCELLED", "closed_at": datetime.now(timezone.utc).isoformat()
                }).eq("state", "WAITING_FOR_ENTRY").lt("generated_at", limit_30).execute()
                count_p = len(res_p.data) if res_p.data else 0
                
                # 2. Clear Stuck Active (ENTRY_HIT > 35m)
                limit_90 = (datetime.now(timezone.utc) - timedelta(minutes=35)).isoformat()
                res_a = db.client.table(settings.TABLE_SIGNALS).update({
                    "state": "TIME_EXIT", "status": "CLOSED_TIMEOUT", "result": "CANCELLED", "closed_at": datetime.now(timezone.utc).isoformat()
                }).eq("state", "ENTRY_HIT").lt("generated_at", limit_90).execute()
                count_a = len(res_a.data) if res_a.data else 0
                
                total = count_p + count_a
                if total > 0:
                    report = (
                        f"✅ *HỆ THỐNG ĐÃ ĐƯỢC GIẢI PHÓNG*\n\n"
                        f"• Đã đóng {count_p} lệnh chờ quá hạn (35m)\n"
                        f"• Đã đóng {count_a} lệnh chạy quá hạn (35m)\n\n"
                        f"🚀 Tổng cộng: `{total}` vật cản đã được dọn dẹp.\n"
                        f"Máy chủ `{settings.INSTANCE_NAME}` đã sẵn sàng bắn tín hiệu mới."
                    )
                else:
                    report = "✅ *HỆ THỐNG SẠCH*\n\nKhông có lệnh nào bị kẹt cần giải phóng."
                
                self._send_to_chat(target_chat_id, report, use_markdown=True)
                
            except Exception as e:
                logger.error(f"Error processing /unblock command: {e}")
                self._send_to_chat(target_chat_id, f"❌ *Lỗi khi giải phóng hệ thống:*\n`{e}`", use_markdown=True)
        else:
            self._send_to_chat(target_chat_id, "❓ *Lệnh không hợp lệ.*\n\n"
                                                "Các lệnh được hỗ trợ: `/status`, `/echo <text>`, `/unblock`", use_markdown=True)

    def _get_updates(self):
        """
        Poll for new updates (messages) from Telegram.
        """
        try:
            params = {"timeout": 30}
            if self._last_update_id:
                params["offset"] = self._last_update_id + 1
            
            response = requests.get(f"https://api.telegram.org/bot{self.bot_token}/getUpdates", params=params, timeout=35)
            response.raise_for_status()
            
            updates = response.json().get("result", [])
            
            if updates:
                for update in updates:
                    self._last_update_id = update["update_id"]
                    if "message" in update:
                        self._process_admin_command(update["message"])
            
            if not self._startup_checked:
                logger.info("Telegram update polling started.")
                self._startup_checked = True
                
        except requests.exceptions.Timeout:
            logger.debug("Telegram getUpdates timed out (normal).")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Telegram updates: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in _get_updates: {e}")

    def reply_to_message(self, message_id: int, text: str) -> Optional[int]:
        """
        Reply to a specific message in the chat.
        
        Args:
            message_id: The ID of the message to reply to.
            text: The reply message text (Markdown formatted).
            
        Returns:
            The message_id of the sent reply, or None if failed.
        """
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown",
                "reply_to_message_id": message_id
            }
            
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            reply_message_id = data.get("result", {}).get("message_id")
            
            logger.success(f"Telegram reply sent successfully (Reply ID: {reply_message_id}, Original ID: {message_id})")
            return reply_message_id
            
        except Exception as e:
            logger.error(f"Failed to send Telegram reply to message {message_id}: {e}")
            return None
    
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
