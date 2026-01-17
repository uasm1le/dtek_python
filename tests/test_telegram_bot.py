"""Tests for Telegram Bot module."""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from telegram_bot import TelegramBot


def test_telegram_bot_initialization():
    """Test Telegram Bot initialization."""
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token_123',
        'TELEGRAM_CHAT_ID': '123456789'
    }):
        bot = TelegramBot()
        assert bot.token == 'test_token_123'
        assert bot.default_chat_id == '123456789'
        print("✓ TelegramBot initialization test passed")


def test_restricted_time_check():
    """Test time-based restriction logic."""
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token_123',
        'TELEGRAM_CHAT_ID': '123456789'
    }):
        bot = TelegramBot()
        
        # Test that method exists and returns boolean
        result = bot._is_restricted_time()
        assert isinstance(result, bool)
        print("✓ Time restriction check method exists and returns bool")


def test_get_time_info():
    """Test get_restricted_time_info method."""
    with patch.dict('os.environ', {
        'TELEGRAM_BOT_TOKEN': 'test_token_123',
        'TELEGRAM_CHAT_ID': '123456789'
    }):
        bot = TelegramBot()
        info = bot.get_restricted_time_info()
        
        assert 'restricted_time_active' in info
        assert 'current_time' in info
        assert 'restriction_window' in info
        assert info['restriction_window'] == "23:30 - 00:30"
        print("✓ Time info retrieval test passed")


if __name__ == "__main__":
    test_telegram_bot_initialization()
    test_restricted_time_check()
    test_get_time_info()
    print("\n✓ All tests passed!")
