import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Hunter.io API Configuration
HUNTER_API_KEY = os.getenv('HUNTER_API_KEY', '1f58b02cc717fa447d6744017e466cd2c51fd649')

# Database Configuration (PythonAnywhere credentials)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '2200032576.mysql.pythonanywhere-services.com'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'database': os.getenv('DB_NAME', '2200032576$default'),
    'user': os.getenv('DB_USER', '2200032576'),
    'password': os.getenv('DB_PASSWORD', 'Aditya@2005'),  # Replace with your actual password
}

# Flask Configuration
FLASK_CONFIG = {
    'DEBUG': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
    'HOST': os.getenv('FLASK_HOST', '0.0.0.0'),
    'PORT': int(os.getenv('FLASK_PORT', 5000)),
}

# Application Settings
APP_CONFIG = {
    'MAX_LEADS_PER_SCRAPE': int(os.getenv('MAX_LEADS_PER_SCRAPE', 100)),
    'SCRAPING_TIMEOUT': int(os.getenv('SCRAPING_TIMEOUT', 30)),
    'RATE_LIMIT_DELAY': float(os.getenv('RATE_LIMIT_DELAY', 1.0)),
    'ENABLE_CACHING': os.getenv('ENABLE_CACHING', 'False').lower() == 'true',
}

# Logging Configuration
LOGGING_CONFIG = {
    'LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
    'FILE': os.getenv('LOG_FILE', 'logs/app.log'),
}

__all__ = [
    'HUNTER_API_KEY',
    'DB_CONFIG',
    'FLASK_CONFIG',
    'APP_CONFIG',
    'LOGGING_CONFIG'
]
