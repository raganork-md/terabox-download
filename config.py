import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API Credentials
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Download Settings
DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 2000 * 1024 * 1024))  # 2GB default
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1024 * 1024))  # 1MB

# Timeout Settings
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 300))  # 5 minutes
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", 3600))  # 1 hour

# Rate Limiting
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
