"""DTEK Python Project Package"""

from dotenv import load_dotenv
import os
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent

# 1. Load base .env
base_env = PROJECT_ROOT / '.env'
if base_env.exists():
    load_dotenv(str(base_env), override=True)

# 2. Load mode-specific .env based on APP_MODE
app_mode = os.getenv('APP_MODE', 'test')
if app_mode == 'test':
    test_env = PROJECT_ROOT / '.env.test'
    if test_env.exists():
        load_dotenv(str(test_env), override=True)
elif app_mode == 'production':
    prod_env = PROJECT_ROOT / '.env.production'
    if prod_env.exists():
        load_dotenv(str(prod_env), override=True)

__version__ = "0.1.0"
