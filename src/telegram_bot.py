"""Telegram Bot Module for sending messages with time-based restrictions."""

import asyncio
from datetime import datetime
from typing import Optional
from telegram import Bot
from telegram.error import TelegramError
import os


class TelegramBot:
    """
    Telegram Bot class for sending messages to chats.
    
    Features:
    - Sends messages to specified chat IDs
    - Time-based restrictions (23:30 - 00:30 requires force_send)
    - Silent mode support
    - Configurable parameters from Config manager
    """

    def __init__(self):
        """Initialize Telegram Bot with credentials from environment variables."""
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.default_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        
        self.bot = Bot(token=self.token)

    def _is_restricted_time(self) -> bool:
        """
        Check if current time is in restricted period (23:30 - 00:30).
        
        Returns:
            bool: True if current time is between 23:30 and 00:30, False otherwise
        """
        now = datetime.now()
        current_time = now.time()
        
        # Define restricted time window: 23:30 to 00:30
        start_time = datetime.strptime("23:30", "%H:%M").time()
        end_time = datetime.strptime("00:30", "%H:%M").time()
        
        # Handle overnight wrap (23:30 to 23:59 and 00:00 to 00:30)
        if start_time <= current_time or current_time <= end_time:
            return True
        
        return False

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        silent_mode: bool = False,
        force_send: bool = False,
    ) -> bool:
        """
        Send a message to Telegram chat with time-based restrictions.
        
        Args:
            text: Message text to send
            chat_id: Target chat ID (uses default if not provided)
            silent_mode: If True, sends message without notification
            force_send: If True, bypasses time restrictions
            
        Returns:
            bool: True if message sent successfully, False otherwise
            
        Raises:
            ValueError: If no chat_id is provided and default is not set
            ValueError: If message cannot be sent during restricted time without force_send
        """
        # Use default chat_id if not provided
        if not chat_id:
            if not self.default_chat_id:
                raise ValueError(
                    "chat_id must be provided or TELEGRAM_CHAT_ID environment variable must be set"
                )
            chat_id = self.default_chat_id

        # Check time-based restrictions
        if self._is_restricted_time() and not force_send:
            raise ValueError(
                "Cannot send message between 23:30 and 00:30 without force_send=True"
            )

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                disable_notification=silent_mode,
            )
            return True
        except TelegramError as e:
            print(f"Error sending message: {e}")
            return False

    def send_message_sync(
        self,
        text: str,
        chat_id: Optional[str] = None,
        silent_mode: bool = False,
        force_send: bool = False,
    ) -> bool:
        """
        Synchronous wrapper for send_message.
        
        Args:
            text: Message text to send
            chat_id: Target chat ID (uses default if not provided)
            silent_mode: If True, sends message without notification
            force_send: If True, bypasses time restrictions
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.send_message(text, chat_id, silent_mode, force_send)
            )
        finally:
            loop.close()

    def get_restricted_time_info(self) -> dict:
        """
        Get information about restricted time window and current status.
        
        Returns:
            dict: Contains restricted_time_active, current_time, and restriction_window
        """
        now = datetime.now()
        return {
            "restricted_time_active": self._is_restricted_time(),
            "current_time": now.strftime("%H:%M:%S"),
            "restriction_window": "23:30 - 00:30",
        }
