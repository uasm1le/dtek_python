"""Power Monitor Database Management using SQLite."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class PowerMonitorDB:
    """SQLite database for power monitoring events."""

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file. Defaults to project root.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / 'power_monitor.db'

        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Power events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS power_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp INTEGER NOT NULL,
                    event_datetime TEXT NOT NULL,
                    duration_seconds INTEGER,
                    message TEXT,
                    draft_confirmed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Stats table (for quick queries)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS power_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    total_outages INTEGER DEFAULT 0,
                    total_offline_seconds INTEGER DEFAULT 0,
                    average_offline_seconds INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # User settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    reminders_enabled BOOLEAN DEFAULT 0,
                    reminder_schedule_today TEXT DEFAULT '09:00',
                    reminder_schedule_tomorrow TEXT DEFAULT '09:00',
                    notifications_enabled BOOLEAN DEFAULT 1,
                    notification_chats TEXT DEFAULT '[]',
                    power_monitor_enabled BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_power_events_timestamp
                ON power_events(timestamp DESC)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_power_events_event_type
                ON power_events(event_type)
            ''')

            conn.commit()

    def add_event(
        self,
        event_type: str,
        timestamp: int,
        duration_seconds: Optional[int] = None,
        message: str = "",
        draft_confirmed: bool = False
    ) -> int:
        """
        Add power event to database.

        Args:
            event_type: 'online', 'offline', or 'draft_confirmed'
            timestamp: Unix timestamp
            duration_seconds: How long device was offline (for offline events)
            message: Event message
            draft_confirmed: Whether draft was confirmed

        Returns:
            Event ID
        """
        event_datetime = datetime.fromtimestamp(timestamp).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO power_events
                (event_type, timestamp, event_datetime, duration_seconds, message, draft_confirmed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event_type, timestamp, event_datetime, duration_seconds, message, draft_confirmed))

            conn.commit()
            return cursor.lastrowid

    def get_events(
        self,
        event_type: Optional[str] = None,
        days: int = 7,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get power events.

        Args:
            event_type: Filter by event type ('online', 'offline', etc.)
            days: Look back N days
            limit: Maximum events to return

        Returns:
            List of event dictionaries
        """
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if event_type:
                cursor.execute('''
                    SELECT * FROM power_events
                    WHERE timestamp > ? AND event_type = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (cutoff_timestamp, event_type, limit))
            else:
                cursor.execute('''
                    SELECT * FROM power_events
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (cutoff_timestamp, limit))

            return [dict(row) for row in cursor.fetchall()]

    def get_recent_offline_duration(self) -> Optional[int]:
        """
        Get duration of most recent offline event.

        Returns:
            Duration in seconds or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT duration_seconds FROM power_events
                WHERE event_type = 'offline'
                ORDER BY timestamp DESC
                LIMIT 1
            ''')

            result = cursor.fetchone()
            return result[0] if result else None

    def get_stats_today(self) -> Dict:
        """
        Get today's statistics.

        Returns:
            Dict with outages count and total offline time
        """
        today = datetime.now().date().isoformat()
        today_start = int(datetime.combine(datetime.now().date(), datetime.min.time()).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get offline events today
            cursor.execute('''
                SELECT COUNT(*) as count, SUM(duration_seconds) as total
                FROM power_events
                WHERE event_type = 'offline' AND timestamp >= ?
            ''', (today_start,))

            result = cursor.fetchone()
            outages_count = result[0] if result[0] else 0
            total_offline = result[1] if result[1] else 0

            return {
                'date': today,
                'outages': outages_count,
                'total_offline_seconds': total_offline,
                'average_offline_seconds': total_offline // outages_count if outages_count > 0 else 0
            }

    def get_stats_range(self, days: int = 30) -> List[Dict]:
        """
        Get statistics for date range.

        Args:
            days: Number of days to look back

        Returns:
            List of daily stats
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).date()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 
                    DATE(datetime(timestamp, 'unixepoch')) as date,
                    COUNT(CASE WHEN event_type = 'offline' THEN 1 END) as outages,
                    SUM(CASE WHEN event_type = 'offline' THEN duration_seconds ELSE 0 END) as total_offline_seconds
                FROM power_events
                WHERE DATE(datetime(timestamp, 'unixepoch')) >= ?
                GROUP BY DATE(datetime(timestamp, 'unixepoch'))
                ORDER BY date DESC
            ''', (str(cutoff_date),))

            stats = []
            for row in cursor.fetchall():
                total_offline = row['total_offline_seconds'] or 0
                outages = row['outages']

                stats.append({
                    'date': row['date'],
                    'outages': outages,
                    'total_offline_seconds': total_offline,
                    'average_offline_seconds': total_offline // outages if outages > 0 else 0
                })

            return stats

    def get_longest_outage(self, days: int = 7) -> Optional[Dict]:
        """
        Get longest offline event in period.

        Args:
            days: Look back N days

        Returns:
            Event dict or None
        """
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM power_events
                WHERE event_type = 'offline' AND timestamp > ?
                ORDER BY duration_seconds DESC
                LIMIT 1
            ''', (cutoff_timestamp,))

            result = cursor.fetchone()
            return dict(result) if result else None

    def get_outage_count_today(self) -> int:
        """Get number of outages today."""
        today_start = int(datetime.combine(datetime.now().date(), datetime.min.time()).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM power_events
                WHERE event_type = 'offline' AND timestamp >= ?
            ''', (today_start,))

            result = cursor.fetchone()
            return result[0] if result[0] else 0

    def cleanup_old_events(self, days: int = 90) -> int:
        """
        Delete events older than N days.

        Args:
            days: Delete events older than this

        Returns:
            Number of deleted rows
        """
        cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM power_events WHERE timestamp < ?', (cutoff_timestamp,))
            conn.commit()

            return cursor.rowcount

    def get_db_size(self) -> int:
        """Get database file size in bytes."""
        if self.db_path.exists():
            return self.db_path.stat().st_size
        return 0

    # ==================== USER SETTINGS ====================

    def get_user_settings(self, user_id: int) -> Dict:
        """Get settings for user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM user_settings WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()

            if result:
                import json
                settings = dict(result)
                # Parse JSON field
                settings['notification_chats'] = json.loads(settings['notification_chats'])
                return settings
            else:
                # Create default settings
                return self.create_user_settings(user_id)

    def create_user_settings(self, user_id: int) -> Dict:
        """Create default settings for new user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR IGNORE INTO user_settings
                (user_id, reminders_enabled, reminder_schedule_today, 
                 reminder_schedule_tomorrow, notifications_enabled, power_monitor_enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, False, '09:00', '09:00', True, True))

            conn.commit()

        return self.get_user_settings(user_id)

    def update_user_settings(self, user_id: int, **kwargs) -> Dict:
        """Update user settings."""
        import json

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Build dynamic UPDATE query
            fields = []
            values = []

            for key, value in kwargs.items():
                if key == 'notification_chats':
                    value = json.dumps(value)
                fields.append(f"{key} = ?")
                values.append(value)

            if not fields:
                return self.get_user_settings(user_id)

            fields.append("updated_at = CURRENT_TIMESTAMP")
            query = f"UPDATE user_settings SET {', '.join(fields)} WHERE user_id = ?"
            values.append(user_id)

            cursor.execute(query, values)
            conn.commit()

        return self.get_user_settings(user_id)

    def set_reminders_enabled(self, user_id: int, enabled: bool):
        """Enable/disable reminders for user."""
        return self.update_user_settings(user_id, reminders_enabled=enabled)

    def set_reminder_schedule_today(self, user_id: int, time: str):
        """Set reminder time for today."""
        return self.update_user_settings(user_id, reminder_schedule_today=time)

    def set_reminder_schedule_tomorrow(self, user_id: int, time: str):
        """Set reminder time for tomorrow."""
        return self.update_user_settings(user_id, reminder_schedule_tomorrow=time)

    def set_power_monitor_enabled(self, user_id: int, enabled: bool):
        """Enable/disable power monitor notifications for user."""
        return self.update_user_settings(user_id, power_monitor_enabled=enabled)

    def set_notifications_enabled(self, user_id: int, enabled: bool):
        """Enable/disable notifications for user."""
        return self.update_user_settings(user_id, notifications_enabled=enabled)

    def add_notification_chat(self, user_id: int, chat_id: int):
        """Add notification chat for user."""
        settings = self.get_user_settings(user_id)
        chats = settings['notification_chats']

        if chat_id not in chats:
            chats.append(chat_id)
            self.update_user_settings(user_id, notification_chats=chats)

    def remove_notification_chat(self, user_id: int, chat_id: int):
        """Remove notification chat for user."""
        settings = self.get_user_settings(user_id)
        chats = settings['notification_chats']

        if chat_id in chats:
            chats.remove(chat_id)
            self.update_user_settings(user_id, notification_chats=chats)