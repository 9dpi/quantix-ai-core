"""
Telegram Notifier v2 - State-Based Message Templates

Sends Telegram notifications for each state transition in the signal lifecycle.
Each state has its own dedicated message template.
"""

import requests
from datetime import datetime
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
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat/channel ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        logger.info(f"TelegramNotifierV2 initialized (chat_id={chat_id})")
    
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
        asset = signal.get("asset", "EURUSD").replace("/", "")
        timeframe = signal.get("timeframe", "M15")
        direction = signal.get("direction", "BUY")
        entry = signal.get("entry_price", 0)
        
        message = (
            f"✅ *ENTRY HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{direction} @ {entry}\n\n"
            f"Status: 📡 LIVE\n"
            f"Now monitoring Take Profit and Stop Loss."
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
        
        message = (
            f"🎯 *TAKE PROFIT HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{direction} @ {entry}\n\n"
            f"Result: ✅ PROFIT"
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
        
        message = (
            f"🛑 *STOP LOSS HIT*\n\n"
            f"{asset} | {timeframe}\n"
            f"{direction} @ {entry}\n\n"
            f"Result: ❌ LOSS"
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
        
        message = (
            f"⚠️ *SIGNAL CANCELLED*\n\n"
            f"{asset} | {timeframe}\n\n"
            f"Price did not reach the entry level within the valid time.\n"
            f"No trade was triggered."
        )
        
        logger.info(f"Sending CANCELLED message for {asset}")
        return self.send_message(message)
    
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

def create_notifier(bot_token: str, chat_id: str) -> TelegramNotifierV2:
    """
    Create a TelegramNotifierV2 instance.
    
    Args:
        bot_token: Telegram bot token
        chat_id: Telegram chat/channel ID
    
    Returns:
        TelegramNotifierV2 instance
    """
    return TelegramNotifierV2(bot_token, chat_id)
