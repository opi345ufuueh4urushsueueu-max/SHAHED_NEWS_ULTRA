"""
SHAHED NEWS ULTRA - Logging System
"""

import logging
import sys
from pathlib import Path
from config import LOG_LEVEL, LOG_FILE


class SecureFormatter(logging.Formatter):
    """Formatter that prevents logging of sensitive information"""

    SENSITIVE_KEYS = [
        "password",
        "token",
        "session",
        "secret",
        "key",
        "auth",
        "phone",
        "otp",
    ]

    def format(self, record):
        # Check message for sensitive data
        if record.msg:
            msg = str(record.msg)
            for key in self.SENSITIVE_KEYS:
                if key.lower() in msg.lower():
                    record.msg = "[SENSITIVE DATA REDACTED]"
                    break

        return super().format(record)


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with file and console handlers"""

    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL.upper())

    # Create formatter
    formatter = SecureFormatter(
        "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not setup file handler: {e}")

    return logger


# Main logger
logger = setup_logger("SHAHED_NEWS_ULTRA")
