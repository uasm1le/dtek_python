"""Tests for Power Monitor module."""

import sys
import os
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from dotenv import load_dotenv

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load test environment
test_env_path = Path(__file__).parent.parent / '.env.test'
load_dotenv(str(test_env_path), override=True)

from src.power_monitor import PowerMonitor
from src.telegram_bot import TelegramBot


@pytest.fixture
def mock_telegram_bot(monkeypatch):
    """Mock Telegram Bot for testing."""
    mock_bot = MagicMock(spec=TelegramBot)
    mock_bot.send_message = AsyncMock()
    
    def mock_init(self):
        self.telegram_bot = mock_bot
        self.access_token = 'test_token_123'
        self.device_id = 'test_device_id'
        self.power_chat_ids = ['123456789']
        self.debug_chat_id = '987654321'
        self.status_file = Path(__file__).parent / '.test_power_status'
        self.log_monitor = True
        self.log_track = True
    
    monkeypatch.setattr(PowerMonitor, '__init__', mock_init)
    return mock_bot


@pytest.fixture
def power_monitor(mock_telegram_bot):
    """Create PowerMonitor instance for testing."""
    monitor = PowerMonitor()
    yield monitor
    # Cleanup
    if monitor.status_file.exists():
        monitor.status_file.unlink()


class TestPowerMonitorInitialization:
    """Test PowerMonitor initialization."""
    
    def test_initialization_with_env_vars(self):
        """Test initialization loads environment variables."""
        with patch.dict('os.environ', {
            'ewelink_accessToken': 'test_access_token',
            'ewelink_deviceId': 'test_device_id',
            'POWER_CHAT_IDS': '123456789,987654321',
            'DEBUG_CHAT_ID': '555555555'
        }):
            monitor = PowerMonitor()
            assert monitor.access_token == 'test_access_token'
            assert monitor.device_id == 'test_device_id'
            assert '123456789' in monitor.power_chat_ids
            assert monitor.debug_chat_id == '555555555'
            print("✓ PowerMonitor initialization test passed")
    
    def test_initialization_missing_credentials(self):
        """Test initialization fails without required credentials."""
        with patch.dict('os.environ', {
            'ewelink_accessToken': '',
            'ewelink_deviceId': ''
        }, clear=True):
            with pytest.raises(ValueError):
                PowerMonitor()
            print("✓ Missing credentials validation test passed")


class TestFormatDuration:
    """Test duration formatting."""
    
    def test_format_seconds(self, power_monitor):
        """Test formatting seconds (less than 1 minute)."""
        result = power_monitor.format_duration(45)  # 45 seconds
        assert '0 хв' in result
        print("✓ Format seconds test passed")
    
    def test_format_45_minutes(self, power_monitor):
        """Test formatting 45 minutes."""
        result = power_monitor.format_duration(2700)  # 45 min
        assert '45 хв' in result
        print("✓ Format 45 minutes test passed")
    
    def test_format_minutes(self, power_monitor):
        """Test formatting minutes."""
        result = power_monitor.format_duration(150)  # 2 min 30 sec
        assert '2 хв' in result
        print("✓ Format minutes test passed")
    
    def test_format_hours(self, power_monitor):
        """Test formatting hours."""
        result = power_monitor.format_duration(3665)  # 1 hour 1 min 5 sec
        assert '1 год.' in result
        assert '1 хв' in result
        print("✓ Format hours test passed")
    
    def test_format_days(self, power_monitor):
        """Test formatting days."""
        result = power_monitor.format_duration(90061)  # 1 day 1 hour 1 min
        assert '1 день' in result
        assert '1 год.' in result
        print("✓ Format days test passed")
    
    def test_format_multiple_days(self, power_monitor):
        """Test formatting multiple days."""
        result = power_monitor.format_duration(259261)  # 3 days 1 hour 1 min
        assert '3 дні' in result
        print("✓ Format multiple days test passed")


class TestStatusFilePersistence:
    """Test status file save and load."""
    
    def test_save_and_load_status(self, power_monitor):
        """Test saving and loading status from file."""
        status_data = {
            'online': True,
            'timestamp': 1234567890,
            'status_changed_at': 1234567800,
            'raw_data': {'test': 'data'}
        }
        
        power_monitor.save_status(status_data)
        loaded_status = power_monitor.load_last_status()
        
        assert loaded_status['online'] == True
        assert loaded_status['timestamp'] == 1234567890
        assert loaded_status['raw_data']['test'] == 'data'
        print("✓ Status persistence test passed")
    
    def test_load_nonexistent_status(self, power_monitor):
        """Test loading status when file doesn't exist."""
        result = power_monitor.load_last_status()
        assert result is None
        print("✓ Load nonexistent status test passed")


class TestPowerStatusCheck:
    """Test power status checking via API."""
    
    @pytest.mark.asyncio
    async def test_check_power_status_online(self, power_monitor):
        """Test checking power status when device is online."""
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            'error': 0,
            'data': {
                'thingList': [{
                    'itemData': {
                        'online': True,
                        'name': 'TestDevice'
                    }
                }]
            }
        })
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await power_monitor.check_power_status()
            
            assert result['online'] == True
            assert 'timestamp' in result
            print("✓ Check power status (online) test passed")
    
    @pytest.mark.asyncio
    async def test_check_power_status_offline(self, power_monitor):
        """Test checking power status when device is offline."""
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            'error': 0,
            'data': {
                'thingList': [{
                    'itemData': {
                        'online': False,
                        'name': 'TestDevice'
                    }
                }]
            }
        })
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock()
            
            result = await power_monitor.check_power_status()
            
            assert result['online'] == False
            print("✓ Check power status (offline) test passed")


class TestMonitoringLogic:
    """Test power monitoring state machine."""
    
    @pytest.mark.asyncio
    async def test_first_run_initialization(self, power_monitor):
        """Test first run - just save status."""
        status = {
            'online': True,
            'timestamp': int(datetime.now().timestamp()),
            'raw_data': {}
        }
        
        with patch.object(power_monitor, 'check_power_status', return_value=status):
            with patch.object(power_monitor, 'save_status') as mock_save:
                await power_monitor.monitor_power_status()
                
                # Should save status on first run
                assert mock_save.called
                print("✓ First run initialization test passed")
    
    @pytest.mark.asyncio
    async def test_online_to_online_no_notification(self, power_monitor):
        """Test online -> online transition (no notification)."""
        current_status = {
            'online': True,
            'timestamp': 1000,
            'raw_data': {}
        }
        last_status = {
            'online': True,
            'timestamp': 900,
            'status_changed_at': 800
        }
        
        with patch.object(power_monitor, 'check_power_status', return_value=current_status):
            with patch.object(power_monitor, 'load_last_status', return_value=last_status):
                with patch.object(power_monitor.telegram_bot, 'send_message') as mock_send:
                    await power_monitor.monitor_power_status()
                    
                    # Should not send any notification
                    assert not mock_send.called
                    print("✓ Online to online (no notification) test passed")
    
    @pytest.mark.asyncio
    async def test_offline_to_online_sends_notification(self, power_monitor):
        """Test offline -> online transition (sends notification)."""
        current_status = {
            'online': True,
            'timestamp': 2000,
            'raw_data': {}
        }
        last_status = {
            'online': False,
            'timestamp': 1000,
            'status_changed_at': 900
        }
        
        with patch.object(power_monitor, 'check_power_status', return_value=current_status):
            with patch.object(power_monitor, 'load_last_status', return_value=last_status):
                with patch.object(power_monitor.telegram_bot, 'send_message', new_callable=AsyncMock) as mock_send:
                    await power_monitor.monitor_power_status()
                    
                    # Should send notification
                    assert mock_send.called
                    call_args = mock_send.call_args
                    assert '💡' in call_args.kwargs['text']  # Check for emoji in message
                    print("✓ Offline to online (sends notification) test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
