"""Telegram Bot Handler with inline menu system."""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, filters

from .database import PowerMonitorDB

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotMenuHandler:
    """Telegram Bot with inline menu system."""

    # Menu callbacks
    CB_MAIN_MENU = "main_menu"
    CB_STATUS = "status"
    CB_SCHEDULE_TODAY = "schedule_today"
    CB_SCHEDULE_TOMORROW = "schedule_tomorrow"
    CB_SETTINGS = "settings"
    CB_NOTIFICATIONS = "settings_notifications"
    CB_REMINDERS = "settings_reminders"
    CB_UPDATE_TOKEN = "settings_update_token"
    CB_LOGS = "settings_logs"
    CB_REMINDERS_TIME_TODAY = "reminders_time_today"
    CB_REMINDERS_TIME_TOMORROW = "reminders_time_tomorrow"
    CB_BACK = "back"

    def __init__(self):
        """Initialize bot."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set")

        self.db = PowerMonitorDB()
        self.app = Application.builder().token(self.token).build()
        self.setup_handlers()

    def setup_handlers(self):
        """Register handlers."""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("menu", self.cmd_menu))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))

    def get_user_settings(self, user_id: int) -> Dict:
        """Get settings for user from database."""
        return self.db.get_user_settings(user_id)

    # ==================== MAIN MENU ====================

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        message = (
            f"Привіт, {user.first_name}! 👋\n\n"
            f"Я монітор статусу світла 💡\n\n"
            f"Натисни меню щоб почати:"
        )
        await self.show_main_menu(update, context, message)

    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /menu command."""
        await self.show_main_menu(update, context, "Головне меню:")

    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str = "Меню:"):
        """Show main menu."""
        keyboard = [
            [InlineKeyboardButton("💡 Поточний статус", callback_data=self.CB_STATUS)],
            [InlineKeyboardButton("📊 Графік на сьогодні", callback_data=self.CB_SCHEDULE_TODAY)],
            [InlineKeyboardButton("📊 Графік на завтра", callback_data=self.CB_SCHEDULE_TOMORROW)],
            [InlineKeyboardButton("⚙️ Налаштування", callback_data=self.CB_SETTINGS)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, reply_markup=reply_markup)

    # ==================== LEVEL 1: STATUS & GRAPHS ====================

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current power status."""
        events = self.db.get_events(limit=1)

        if not events:
            text = "📊 Немає даних про статус"
        else:
            last_event = events[0]
            event_type = last_event['event_type']
            timestamp = last_event['timestamp']
            event_time = datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")

            if event_type == 'online':
                emoji = "🟢"
                status = "СВІТЛО ВКЛ"
            elif event_type == 'offline':
                emoji = "🔴"
                status = "СВІТЛО ВИМ"
            else:
                emoji = "⚠️"
                status = "НЕВІДОМО"

            duration = last_event.get('duration_seconds')
            duration_str = self.format_duration(duration) if duration else "—"

            text = (
                f"{emoji} <b>{status}</b>\n\n"
                f"⏰ Час: {event_time}\n"
                f"⏱️ Тривалість: {duration_str}"
            )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_schedule_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show today's schedule (placeholder)."""
        text = (
            "📊 <b>Графік на сьогодні</b>\n\n"
            "⚠️ Графік будуть додатися пізніше"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_schedule_tomorrow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show tomorrow's schedule (placeholder)."""
        text = (
            "📊 <b>Графік на завтра</b>\n\n"
            "⚠️ Графік будуть додатися пізніше"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_MAIN_MENU)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # ==================== LEVEL 2: SETTINGS ====================

    async def handle_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings menu."""
        text = "⚙️ <b>Налаштування</b>"

        keyboard = [
            [InlineKeyboardButton("🔔 Оповіщення в чати", callback_data=self.CB_NOTIFICATIONS)],
            [InlineKeyboardButton("🔕 Нагадування", callback_data=self.CB_REMINDERS)],
            [InlineKeyboardButton("🔑 Оновити токен еелінк", callback_data=self.CB_UPDATE_TOKEN)],
            [InlineKeyboardButton("📝 Логи", callback_data=self.CB_LOGS)],
            [InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_MAIN_MENU)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show notifications settings."""
        user_id = update.effective_user.id
        user_settings = self.get_user_settings(user_id)
        status = "✅ Включено" if user_settings['notifications_enabled'] else "❌ Відключено"

        text = (
            f"🔔 <b>Оповіщення в чати</b>\n\n"
            f"Статус: {status}\n\n"
            f"Чати: {', '.join(map(str, user_settings['notification_chats'])) or 'Не встановлено'}"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_SETTINGS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_reminders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reminders menu."""
        user_id = update.effective_user.id
        user_settings = self.get_user_settings(user_id)
        status = "✅ Включено" if user_settings['reminders_enabled'] else "❌ Відключено"

        text = (
            f"🔕 <b>Нагадування</b>\n\n"
            f"Статус: {status}"
        )

        keyboard = [
            [InlineKeyboardButton("📊 Час для сьогодні", callback_data=self.CB_REMINDERS_TIME_TODAY)],
            [InlineKeyboardButton("📊 Час для завтра", callback_data=self.CB_REMINDERS_TIME_TOMORROW)],
            [InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_SETTINGS)],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_reminders_time_today(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show time selection for today's reminders."""
        user_id = update.effective_user.id
        user_settings = self.get_user_settings(user_id)
        current_time = user_settings['reminder_schedule_today']

        text = (
            f"🕐 <b>Вибери час для нагадування (сьогодні)</b>\n\n"
            f"Поточний час: {current_time}"
        )

        # Time options
        times = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
        keyboard = []
        for i in range(0, len(times), 2):
            row = [InlineKeyboardButton(times[i], callback_data=f"time_today_{times[i]}")]
            if i + 1 < len(times):
                row.append(InlineKeyboardButton(times[i + 1], callback_data=f"time_today_{times[i + 1]}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_REMINDERS)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_reminders_time_tomorrow(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show time selection for tomorrow's reminders."""
        user_id = update.effective_user.id
        user_settings = self.get_user_settings(user_id)
        current_time = user_settings['reminder_schedule_tomorrow']

        text = (
            f"🕐 <b>Вибери час для нагадування (завтра)</b>\n\n"
            f"Поточний час: {current_time}"
        )

        # Time options
        times = ["06:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
        keyboard = []
        for i in range(0, len(times), 2):
            row = [InlineKeyboardButton(times[i], callback_data=f"time_tomorrow_{times[i]}")]
            if i + 1 < len(times):
                row.append(InlineKeyboardButton(times[i + 1], callback_data=f"time_tomorrow_{times[i + 1]}"))
            keyboard.append(row)

        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_REMINDERS)])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_update_token(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show update token dialog."""
        text = (
            "🔑 <b>Оновити токен еелінк</b>\n\n"
            "⚠️ Функція буде реалізована пізніше"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_SETTINGS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    async def handle_logs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show logs."""
        text = (
            "📝 <b>Логи</b>\n\n"
            "⚠️ Функція буде реалізована пізніше"
        )

        keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_SETTINGS)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='HTML')

    # ==================== CALLBACK ROUTER ====================

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback queries."""
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        # Main menu
        if callback_data == self.CB_MAIN_MENU:
            await self.show_main_menu(update, context, "Головне меню:")

        # Level 1
        elif callback_data == self.CB_STATUS:
            await self.handle_status(update, context)
        elif callback_data == self.CB_SCHEDULE_TODAY:
            await self.handle_schedule_today(update, context)
        elif callback_data == self.CB_SCHEDULE_TOMORROW:
            await self.handle_schedule_tomorrow(update, context)

        # Level 2
        elif callback_data == self.CB_SETTINGS:
            await self.handle_settings(update, context)
        elif callback_data == self.CB_NOTIFICATIONS:
            await self.handle_notifications(update, context)
        elif callback_data == self.CB_REMINDERS:
            await self.handle_reminders(update, context)
        elif callback_data == self.CB_UPDATE_TOKEN:
            await self.handle_update_token(update, context)
        elif callback_data == self.CB_LOGS:
            await self.handle_logs(update, context)

        # Level 3
        elif callback_data == self.CB_REMINDERS_TIME_TODAY:
            await self.handle_reminders_time_today(update, context)
        elif callback_data == self.CB_REMINDERS_TIME_TOMORROW:
            await self.handle_reminders_time_tomorrow(update, context)

        # Time selections
        elif callback_data.startswith("time_today_"):
            time_value = callback_data.replace("time_today_", "")
            user_id = update.effective_user.id
            self.db.set_reminder_schedule_today(user_id, time_value)
            await query.edit_message_text(
                f"✅ Час для сьогодні встановлено: {time_value}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_REMINDERS)]])
            )

        elif callback_data.startswith("time_tomorrow_"):
            time_value = callback_data.replace("time_tomorrow_", "")
            user_id = update.effective_user.id
            self.db.set_reminder_schedule_tomorrow(user_id, time_value)
            await query.edit_message_text(
                f"✅ Час для завтра встановлено: {time_value}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data=self.CB_REMINDERS)]])
            )

    def format_duration(self, seconds: int) -> str:
        """Format duration in Ukrainian."""
        if not seconds:
            return "0 хв"

        total_minutes = seconds // 60
        total_hours = total_minutes // 60
        days = total_hours // 24
        hours = total_hours % 24
        minutes = total_minutes % 60

        parts = []

        if days > 0:
            day_word = 'день' if days == 1 else ('дні' if 2 <= days <= 4 else 'днів')
            parts.append(f"{days} {day_word}")

        if hours > 0:
            parts.append(f"{hours} год.")

        if minutes > 0 or (days == 0 and hours == 0):
            parts.append(f"{minutes} хв")

        return ' '.join(parts)

    async def setup_commands(self):
        """Set bot commands."""
        commands = [
            BotCommand("start", "Початок"),
            BotCommand("menu", "Меню"),
        ]
        await self.app.bot.set_my_commands(commands)

    async def start(self):
        """Start bot."""
        logger.info("🤖 Telegram Bot Handler starting...")
        await self.setup_commands()
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()
        logger.info("✅ Bot is running. Press Ctrl+C to stop.")

    async def stop(self):
        """Stop bot."""
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()


async def run_bot():
    """Run bot."""
    handler = BotMenuHandler()
    try:
        await handler.start()
    except KeyboardInterrupt:
        logger.info("⏹️ Bot stopped")
        await handler.stop()


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_bot())
