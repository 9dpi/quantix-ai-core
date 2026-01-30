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
            
            logger.success("Telegram message sent successfully")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    # ========================================
    # STATE-SPECIFIC MESSAGE METHODS
    # ========================================
    
    def send_waiting_for_entry(self, signal: dict) -> bool:
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
        confidence = int(signal.get("ai_confidence", 0) * 100)
        
        # Format expiry time
        expiry_str = self._format_expiry_time(signal.get("expiry_at"))
        
        # Direction emoji
        dir_emoji = "🟢" if direction == "BUY" else "🔴"
        
        message = (
            f"🚨 *NEW SIGNAL*\n\n"
            f"Asset: {asset}\n"
            f"Timeframe: {timeframe}\n"
            f"Direction: {dir_emoji} {direction}\n\n"
            f"Status: ⏳ WAITING FOR ENTRY\n"
            f"Entry Price: {entry}\n"
            f"Take Profit: {tp}\n"
            f"Stop Loss: {sl}\n\n"
            f"Confidence: {confidence}%\n"
            f"Valid Until: {expiry_str}\n\n"
            f"⚠️ This signal is waiting for price to reach the entry level."
        )
        
        logger.info(f"Sending WAITING_FOR_ENTRY message for {asset}")
        return self.send_message(message)
    
    def send_entry_hit(self, signal: dict) -> bool:
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
        
        message = (
            f"📍 *ENTRY PRICE HIT*\n\n"
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
        return self.send_message(message)
    
    def send_tp_hit(self, signal: dict) -> bool:
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
        
        # Rule: BLOCK if ENTRY_HIT was not sent by this instance
        signal_id = signal.get("id")
        if signal_id not in self._notified_entries:
            logger.warning(f"⛔ Blocked TP_HIT for {signal_id} (Orphan: Entry not notified)")
            return False
        
        message = (
            f"✅ *TAKE PROFIT HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"TP: {signal.get('tp')}\n\n"
            f"Result: 🟢 PROFIT\n"
            f"R:R: 1 : 1\n\n"
            f"Signal lifecycle completed."
        )
        
        logger.info(f"Sending TP_HIT message for {asset}")
        return self.send_message(message)
    
    def send_sl_hit(self, signal: dict) -> bool:
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
        
        # Rule: BLOCK if ENTRY_HIT was not sent by this instance
        signal_id = signal.get("id")
        if signal_id not in self._notified_entries:
            logger.warning(f"⛔ Blocked SL_HIT for {signal_id} (Orphan: Entry not notified)")
            return False
        
        message = (
            f"🛑 *STOP LOSS HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Entry: {entry}\n"
            f"SL: {signal.get('sl')}\n\n"
            f"Result: 🔴 LOSS\n\n"
            f"Signal lifecycle completed."
        )
        
        logger.info(f"Sending SL_HIT message for {asset}")
        return self.send_message(message)
    
    def send_cancelled(self, signal: dict) -> bool:
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
        
        message = (
            f"⚪ *SIGNAL EXPIRED*\n\n"
            f"{asset} | {timeframe}\n"
            f"{dir_emoji} {direction}\n\n"
            f"Status: NOT TRIGGERED\n"
            f"Entry price was not reached.\n\n"
            f"No trade taken."
        )
        
        logger.info(f"Sending CANCELLED message for {asset}")
        return self.send_message(message)

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
        for update in updates:
            self._last_update_id = update['update_id'] + 1
            
            message = update.get("message")
            if not message or "text" not in message: continue
            
            # Security: Robust Chat ID comparison
            current_chat_id = str(message['chat']['id']).strip()
            target_admin_id = str(self.admin_chat_id).strip()
            
            if current_chat_id != target_admin_id:
                logger.warning(f"🚫 Ignored command from unauthorized ID: {current_chat_id}")
                continue

            text = message.get("text", "").strip()
            logger.info(f"📩 CMD RECEIVED: {text}")
            
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
                signals = getattr(watcher, 'last_watched_count', 0) if watcher else "N/A"
                status_text = (
                    "📊 BÁO CÁO HỆ THỐNG\n\n"
                    f"Máy chủ: {instance}\n"
                    f"Tiến trình: Đang canh {signals} cặp tiền\n"
                    f"Thời gian: {datetime.utcnow().strftime('%H:%M:%S UTC')}"
                )
                self._send_to_chat(target_chat_id, status_text, use_markdown=False)

            elif cmd == "/signal" or cmd == "/signals":
                count = getattr(watcher, 'last_watched_count', 0) if watcher else 0
                self._send_to_chat(target_chat_id, f"🔍 TRA CỨU: Hệ thống đang canh chừng {count} cặp tiền. Mọi thứ đều ổn định.", use_markdown=False)
            
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
