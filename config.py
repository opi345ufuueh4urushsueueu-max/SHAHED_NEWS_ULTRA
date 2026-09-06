"""
SHAHED NEWS ULTRA - Configuration Management
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"

# Create directories if not exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Rubika Configuration
RUBIKA_PHONE = os.getenv("RUBIKA_PHONE", "")
RUBIKA_PASSWORD = os.getenv("RUBIKA_PASSWORD", "")

# Destination Configuration
DESTINATION_CHANNEL = os.getenv("DESTINATION_CHANNEL", "")
DESTINATION_CHANNEL_ID = os.getenv("DESTINATION_CHANNEL_ID", "")

# Owner Configuration
OWNER_ID = os.getenv("OWNER_ID", "")

# Database Configuration
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "shahed_news.db"))

# System Settings
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_BACKOFF = int(os.getenv("RETRY_BACKOFF", "2"))

# Features
SEND_STARTUP_MESSAGE = os.getenv("SEND_STARTUP_MESSAGE", "true").lower() == "true"
STARTUP_MESSAGE_COOLDOWN = int(os.getenv("STARTUP_MESSAGE_COOLDOWN", "3600"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "shahed_news.log"

# API Limitations
API_LIMITATIONS = {
    "library": "rubpy",
    "version": "2.0.0",
    "is_official": False,
    "authentication_method": "Phone + Password + OTP",
    "session_based": True,
    "supported_features": [
        "Connect to Rubika account",
        "Access public channel messages",
        "Send messages to channels",
        "Receive message updates",
    ],
    "unsupported_features": [
        "Official API search",
        "Direct channel discovery",
        "Rate limit guarantee",
        "API stability guarantee",
    ],
    "warnings": [
        "Unofficial library - may break anytime",
        "Phone authentication required",
        "Possible TOS violation",
        "Use at your own risk",
    ],
}
