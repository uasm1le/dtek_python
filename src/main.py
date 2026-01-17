"""DTEK Python Project - Main Module"""

import sys
import os

# src/__init__.py завантажує .env автоматично
import src
from src.telegram_bot import TelegramBot


def hello():
    """Print a greeting message."""
    print("Hello from DTEK Python Project!")
    return "Hello, World!"


def display_mode_menu():
    """Display available environment modes."""
    print("\n" + "="*50)
    print("ENVIRONMENT MODE SELECTOR")
    print("="*50)
    print("Available modes:")
    print("  1. development (default) - Local development")
    print("  2. test - Testing environment")
    print("  3. production - Production environment")
    print("="*50)


def select_mode():
    """Allow user to select environment mode."""
    display_mode_menu()
    
    current_mode = os.getenv('APP_MODE', 'development')
    print(f"\nCurrent mode: {current_mode}")
    
    choice = input("\nSelect mode (1-3) or press Enter to keep current: ").strip()
    
    mode_map = {
        '1': 'development',
        '2': 'test',
        '3': 'production',
    }
    
    if choice in mode_map:
        return mode_map[choice]
    
    return current_mode


def demonstrate_telegram_bot():
    """Demonstrate Telegram Bot usage."""
    print("\n" + "-"*50)
    print("TELEGRAM BOT STATUS")
    print("-"*50)
    
    try:
        bot = TelegramBot()
        
        # Show configuration
        print(f"Bot Token: {os.getenv('TELEGRAM_BOT_TOKEN')[:20]}***")
        print(f"Chat ID: {os.getenv('TELEGRAM_CHAT_ID')}")
        print(f"App Mode: {os.getenv('APP_MODE', 'development')}")
        print(f"Debug: {os.getenv('DEBUG', 'False')}")
        print(f"Log Level: {os.getenv('LOG_LEVEL', 'INFO')}")
        
    except ValueError as e:
        print(f"Telegram Bot Error: {e}")


def main():
    """Main entry point."""
    hello()
    
    # Show mode selection
    selected_mode = select_mode()
    
    # If mode changed, set it and restart
    if selected_mode != os.getenv('APP_MODE', 'development'):
        os.environ['APP_MODE'] = selected_mode
        print(f"\n✓ Switched to {selected_mode} mode")
        # Note: In real app, would need to reimport modules
    
    # Demonstrate bot functionality
    demonstrate_telegram_bot()
    
    print("\n" + "="*50)
    print("Setup complete!")
    print("="*50)


if __name__ == "__main__":
    main()



