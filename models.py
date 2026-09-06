"""
SHAHED NEWS ULTRA - Data Models
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Source:
    """Channel source model"""
    id: int
    channel_username: str
    channel_id: int
    channel_name: str
    enabled: bool = True
    last_message_id: Optional[int] = None
    last_checked: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


@dataclass
class News:
    """News article model"""
    id: int
    message_id: int
    source_id: int
    source_name: str
    message_date: datetime
    original_text: str
    original_link: Optional[str] = None
    text_hash: str = ""
    normalized_text_hash: str = ""
    is_breaking_news: bool = False
    published: bool = False
    published_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Admin:
    """Admin user model"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    permission_level: str = "ADMIN"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SystemState:
    """System state model"""
    collector_running: bool = False
    publisher_running: bool = False
    connection_status: str = "DISCONNECTED"  # CONNECTED, RECONNECTING, ERROR
    last_startup: Optional[datetime] = None
    total_news_received: int = 0
    total_news_published: int = 0
    duplicate_count: int = 0
    error_count: int = 0


@dataclass
class ProcessedNews:
    """Processed news ready for publishing"""
    message_id: int
    source_name: str
    original_text: str
    original_link: Optional[str]
    is_breaking_news: bool
    text_hash: str
    normalized_text_hash: str
    message_parts: List[str] = field(default_factory=list)
    part_count: int = 1
