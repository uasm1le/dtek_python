"""Configuration manager for handling different environments."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration manager for development, test, and production environments.
    
    Loads environment variables from appropriate .env file based on APP_MODE.
    """

    # Valid modes
    MODES = {
        'development': '.env',
        'test': '.env.test',
        'production': '.env.production',
    }

    def __init__(self, mode: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            mode: Environment mode ('development', 'test', 'production')
                  If None, uses APP_MODE from current environment or defaults to 'development'
        """
        # Get mode from parameter or environment variable or default
        self.mode = mode or os.getenv('APP_MODE', 'development')
        
        if self.mode not in self.MODES:
            raise ValueError(
                f"Invalid APP_MODE '{self.mode}'. Must be one of: {', '.join(self.MODES.keys())}"
            )
        
        # Set ENVIRONMENT based on APP_MODE
        os.environ['ENVIRONMENT'] = self.mode
        
        # Load the appropriate .env file
        self._load_env_file()

    def _load_env_file(self):
        """Load environment variables from the appropriate .env file."""
        # First, load .env (base/common variables)
        base_env_path = Path(__file__).parent.parent / '.env'
        if base_env_path.exists():
            load_dotenv(base_env_path, override=False)
        
        # Then, load mode-specific file (overrides)
        env_file = self.MODES[self.mode]
        env_path = Path(__file__).parent.parent / env_file
        
        if env_path.exists() and env_file != '.env':
            load_dotenv(env_path, override=True)
            print(f"Loaded configuration: .env + {env_file} (mode: {self.mode})")
        else:
            print(f"Loaded configuration from .env (mode: {self.mode})")

    @staticmethod
    def get_mode() -> str:
        """Get current application mode."""
        return os.getenv('APP_MODE', 'development')

    @staticmethod
    def get_telegram_token() -> str:
        """Get Telegram bot token."""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment")
        return token

    @staticmethod
    def get_telegram_chat_id() -> str:
        """Get default Telegram chat ID."""
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID not found in environment")
        return chat_id

    @staticmethod
    def is_debug() -> bool:
        """Check if debug mode is enabled."""
        return os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

    @staticmethod
    def get_log_level() -> str:
        """Get logging level."""
        return os.getenv('LOG_LEVEL', 'INFO')

    @staticmethod
    def get_environment() -> str:
        """Get environment name."""
        return os.getenv('ENVIRONMENT', 'development')

    @classmethod
    def switch_mode(cls, mode: str) -> 'Config':
        """
        Switch to a different environment mode.
        
        Args:
            mode: New mode ('development', 'test', 'production')
            
        Returns:
            Config: New Config instance with switched mode
        """
        if mode not in cls.MODES:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(cls.MODES.keys())}"
            )
        return cls(mode=mode)

    def __repr__(self) -> str:
        """String representation of config."""
        return (
            f"Config(mode={self.mode}, "
            f"debug={self.is_debug()}, "
            f"log_level={self.get_log_level()})"
        )

    def get_all_settings(self) -> dict:
        """Get all current settings."""
        return {
            'mode': self.mode,
            'environment': self.get_environment(),
            'debug': self.is_debug(),
            'log_level': self.get_log_level(),
            'bot_token': self.get_telegram_token()[:10] + '***' if self.get_telegram_token() else None,
            'chat_id': self.get_telegram_chat_id(),
        }
