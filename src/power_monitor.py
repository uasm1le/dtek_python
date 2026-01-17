"""Power Status Monitor with eWelink API integration."""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import httpx

from .telegram_bot import TelegramBot


class PowerMonitor:
    """
    Monitor power status via eWelink API with draft confirmation mode.
    
    Features:
    - Queries eWelink API for device status
    - 10-minute draft mode to confirm power outages
    - Prevents false positives from brief interruptions
    - Sends notifications to Telegram
    - Saves status to JSON file for persistence
    """

    # 10 minutes confirmation delay
    POWER_OFF_CONFIRMATION_DELAY = 10 * 60  # seconds

    def __init__(self):
        """
        Initialize Power Monitor.
        """
        self.telegram_bot = TelegramBot()
        
        # Get credentials from environment
        self.access_token = os.getenv('ewelink_accessToken')
        self.device_id = os.getenv('ewelink_deviceId')
        
        if not self.access_token or not self.device_id:
            raise ValueError("ewelink_accessToken and ewelink_deviceId must be set in environment")
        
        # Parse power chat IDs (comma-separated)
        power_chat_ids_str = os.getenv('POWER_CHAT_IDS', '')
        self.power_chat_ids = [cid.strip() for cid in power_chat_ids_str.split(',') if cid.strip()]
        
        # Debug chat ID
        self.debug_chat_id = os.getenv('DEBUG_CHAT_ID')
        
        # Status file location
        self.status_file = Path(__file__).parent.parent / '.power_status'
        
        # Logging flags
        debug_mode = os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')
        self.log_monitor = debug_mode or os.getenv('LOG_POWER', 'false').lower() == 'true'
        self.log_track = debug_mode or os.getenv('TRACK_POWER_DRAFT', 'false').lower() == 'true'

    async def check_power_status(self) -> Optional[Dict[str, Any]]:
        """
        Check device power status via ewelink API.
        
        Returns:
            dict with keys: online (bool), timestamp (int), rawData (dict)
            None if request fails
        """
        try:
            request_body = {
                "thingList": [
                    {
                        "itemType": 1,
                        "id": self.device_id
                    }
                ]
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    'https://apia.coolkit.cn/v2/device/thing',
                    json=request_body,
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.access_token}'
                    },
                    timeout=10.0
                )
            
            data = response.json()
            
            if self.log_monitor:
                self._log_api_call('check_power_status', request_body, data)
            
            # Extract online status from response
            device = data.get('data', {}).get('thingList', [{}])[0]
            is_online = device.get('itemData', {}).get('online') is True
            
            return {
                'online': is_online,
                'timestamp': int(datetime.now().timestamp()),
                'raw_data': device
            }
            
        except Exception as error:
            print(f"❌ Failed to check power status: {str(error)}")
            return None

    def load_last_status(self) -> Optional[Dict[str, Any]]:
        """
        Load last known power status from file.
        
        Returns:
            dict with last status or None if file doesn't exist
        """
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    return json.load(f)
        except Exception as error:
            print(f"❌ Failed to load last status: {str(error)}")
        
        return None

    def save_status(self, status: Dict[str, Any]):
        """
        Save current power status to file.
        
        Args:
            status: Status dictionary to save
        """
        try:
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
        except Exception as error:
            print(f"❌ Failed to save status: {str(error)}")

    def _log_api_call(self, method_name: str, request: Dict, response: Dict):
        """Log API call for debugging."""
        timestamp = datetime.now().isoformat()
        print(f"\n[{timestamp}] POWER_MONITOR.{method_name}()")
        print(f"📤 Request: {json.dumps(request, indent=2)}")
        print(f"📥 Response: {json.dumps(response, indent=2)}")

    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        Format duration in Ukrainian.
        
        Args:
            seconds: Duration in seconds
            
        Returns:
            Formatted string (e.g., "2 дні 3 год. 45 хв")
        """
        total_minutes = seconds // 60
        total_hours = total_minutes // 60
        days = total_hours // 24
        hours = total_hours % 24
        minutes = total_minutes % 60
        
        parts = []
        
        if days > 0:
            if days == 1:
                day_word = 'день'
            elif 2 <= days <= 4:
                day_word = 'дні'
            else:
                day_word = 'днів'
            parts.append(f"{days} {day_word}")
        
        if hours > 0:
            parts.append(f"{hours} год.")
        
        if minutes > 0 or (days == 0 and hours == 0):
            parts.append(f"{minutes} хв")
        
        return ' '.join(parts)

    async def monitor_power_status(self):
        """
        Monitor power status and send notifications on changes.
        
        Implements state machine:
        - online → online: No action
        - offline → offline: No action
        - online → offline: Activate draft mode (10 min wait)
        - offline → online: Send notification immediately
        """
        current_status = await self.check_power_status()
        
        if not current_status:
            if self.log_monitor:
                print("⚠️  Could not check power status")
            return
        
        last_status = self.load_last_status()
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        
        # First run - just save status
        if not last_status:
            self.save_status({
                'online': current_status['online'],
                'timestamp': current_status['timestamp'],
                'status_changed_at': current_status['timestamp'],
                'raw_data': current_status['raw_data']
            })
            if self.log_monitor:
                print(f"[{time_str}] 📍 Initial power status: {'🟢 Online' if current_status['online'] else '🔴 Offline'}")
            return
        
        # Both online - no change
        if last_status.get('online') and current_status['online']:
            self.save_status({
                'online': current_status['online'],
                'timestamp': current_status['timestamp'],
                'status_changed_at': last_status.get('status_changed_at'),
                'raw_data': current_status['raw_data']
            })
            return
        
        # Both offline - no change
        if not last_status.get('online') and not current_status['online']:
            self.save_status({
                'online': current_status['online'],
                'timestamp': current_status['timestamp'],
                'status_changed_at': last_status.get('status_changed_at'),
                'raw_data': current_status['raw_data']
            })
            return
        
        # Offline → Online: Send notification immediately
        if not last_status.get('online') and current_status['online']:
            duration = current_status['timestamp'] - last_status.get('status_changed_at', current_status['timestamp'])
            duration_str = self.format_duration(duration)
            message = f"💡 {time_str} Юху! Світло повернулося!\n⏱️ Було відсутнє {duration_str}"
            
            for chat_id in self.power_chat_ids:
                await self.telegram_bot.send_message(
                    text=message,
                    chat_id=chat_id,
                    silent_mode=False,
                    force_send=True
                )
            
            # Debug notification if in draft mode
            if last_status.get('draft_off_time') and self.log_track and self.debug_chat_id:
                draft_duration = current_status['timestamp'] - last_status.get('draft_off_time')
                draft_duration_str = self.format_duration(draft_duration)
                debug_message = (
                    f"ℹ️ <b>DRAFT СКАСОВАНО</b>\n\n"
                    f"💡 Світло повернулось за {draft_duration_str} від початку draft"
                )
                await self.telegram_bot.send_message(
                    text=debug_message,
                    chat_id=self.debug_chat_id,
                    silent_mode=True,
                    force_send=True
                )
            
            self.save_status({
                'online': current_status['online'],
                'timestamp': current_status['timestamp'],
                'status_changed_at': current_status['timestamp'],
                'raw_data': current_status['raw_data']
            })
            return
        
        # Online → Offline: Activate draft mode
        if last_status.get('online') and not current_status['online']:
            # First time power off - start draft
            if not last_status.get('draft_off_time'):
                self.save_status({
                    'online': True,  # Still consider online
                    'timestamp': current_status['timestamp'],
                    'status_changed_at': last_status.get('status_changed_at'),
                    'draft_off_time': current_status['timestamp'],
                    'raw_data': current_status['raw_data']
                })
                
                # Debug notification
                if self.log_track and self.debug_chat_id:
                    draft_message = (
                        f"⚠️ <b>DRAFT: Потенційне вимкнення світла</b>\n\n"
                        f"🕐 Час виявлення: {time_str}\n"
                        f"⏳ Очікуємо підтвердження (10 хвилин)..."
                    )
                    await self.telegram_bot.send_message(
                        text=draft_message,
                        chat_id=self.debug_chat_id,
                        silent_mode=True,
                        force_send=True
                    )
                
                if self.log_monitor:
                    print(f"[{time_str}] ⚠️ Світло потенційно вимкнулось (draft режим). Чекаємо 10 хвилин...")
                
                return
            
            # Draft already active - check if confirmation delay passed
            time_since_draft = current_status['timestamp'] - last_status.get('draft_off_time', current_status['timestamp'])
            
            if time_since_draft >= self.POWER_OFF_CONFIRMATION_DELAY:
                # Delay passed - confirm power outage
                duration = current_status['timestamp'] - last_status.get('status_changed_at', current_status['timestamp'])
                duration_str = self.format_duration(duration)
                message = f"🔦 {time_str} Йой… Халепа, знову без світла 😒\n⏱️ Було наявне {duration_str}"
                
                for chat_id in self.power_chat_ids:
                    await self.telegram_bot.send_message(
                        text=message,
                        chat_id=chat_id,
                        silent_mode=False,
                        force_send=True
                    )
                
                # Debug notification
                if self.log_track and self.debug_chat_id:
                    debug_message = (
                        f"✅ <b>DRAFT ПІДТВЕРДЖЕНО</b>\n\n"
                        f"🔦 Вимкнення світла підтверджено після 10 хвилин"
                    )
                    await self.telegram_bot.send_message(
                        text=debug_message,
                        chat_id=self.debug_chat_id,
                        silent_mode=True,
                        force_send=True
                    )
                
                self.save_status({
                    'online': False,
                    'timestamp': current_status['timestamp'],
                    'status_changed_at': current_status['timestamp'],
                    'raw_data': current_status['raw_data']
                })
            else:
                # Still waiting for confirmation
                remaining = self.POWER_OFF_CONFIRMATION_DELAY - time_since_draft
                if self.log_monitor:
                    print(f"[{time_str}] ⚠️ Все ще без світла... (чекаємо ще {remaining}с)")

    def run(self):
        """
        Run power monitor synchronously (for cron jobs).
        
        Example cron entry:
        */1 * * * * cd /path/to/project && python -c "from src.power_monitor import PowerMonitor; PowerMonitor().run()"
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.monitor_power_status())
        finally:
            loop.close()

    async def start_monitoring(self, interval_minutes: int = 1):
        """
        Start periodic power monitoring (for long-running processes).
        
        Args:
            interval_minutes: Check interval in minutes
        """
        print(f"🔌 Starting power monitoring (checking every {interval_minutes} minute(s))...")
        
        # Initial check
        await self.monitor_power_status()
        
        # Periodic checks
        while True:
            await asyncio.sleep(interval_minutes * 60)
            await self.monitor_power_status()
