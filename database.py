"""
SHAHED NEWS ULTRA - Database Management
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from logger import logger
from config import DATABASE_PATH
from models import Source, News, Admin, SystemState


class Database:
    """SQLite database manager"""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.conn = None
        self.init_db()

    def connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def init_db(self):
        """Initialize database tables"""
        self.connect()
        cursor = self.conn.cursor()

        try:
            # Sources table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_username TEXT UNIQUE NOT NULL,
                    channel_id INTEGER,
                    channel_name TEXT,
                    enabled BOOLEAN DEFAULT 1,
                    last_message_id INTEGER,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

            # News table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER UNIQUE NOT NULL,
                    source_id INTEGER NOT NULL,
                    source_name TEXT,
                    message_date TIMESTAMP,
                    original_text TEXT,
                    original_link TEXT,
                    text_hash TEXT UNIQUE,
                    normalized_text_hash TEXT,
                    is_breaking_news BOOLEAN DEFAULT 0,
                    published BOOLEAN DEFAULT 0,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(id)
                )
            """)

            # Admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    user_name TEXT,
                    permission_level TEXT DEFAULT 'ADMIN',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Error logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    error_message TEXT,
                    source_id INTEGER,
                    traceback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_message_id ON news(message_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_id ON news(source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_text_hash ON news(text_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_published ON news(published)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_username ON sources(channel_username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_source_enabled ON sources(enabled)")

            self.conn.commit()
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def add_source(self, source: Source) -> int:
        """Add a new source"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO sources 
                (channel_username, channel_id, channel_name, enabled, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                source.channel_username,
                source.channel_id,
                source.channel_name,
                source.enabled,
                datetime.now()
            ))
            self.conn.commit()
            logger.info(f"Source added: {source.channel_username}")
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.warning(f"Source already exists: {source.channel_username}")
            return -1
        except Exception as e:
            logger.error(f"Failed to add source: {e}")
            return -1

    def get_sources(self, enabled_only: bool = False) -> List[Source]:
        """Get all sources"""
        cursor = self.conn.cursor()
        try:
            if enabled_only:
                cursor.execute("SELECT * FROM sources WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM sources")
            
            rows = cursor.fetchall()
            sources = []
            for row in rows:
                sources.append(Source(
                    id=row[0],
                    channel_username=row[1],
                    channel_id=row[2],
                    channel_name=row[3],
                    enabled=bool(row[4]),
                    last_message_id=row[5],
                    last_checked=row[6],
                    created_at=row[7],
                    updated_at=row[8]
                ))
            return sources
        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return []

    def update_source_last_message(self, source_id: int, message_id: int):
        """Update last message ID for a source"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE sources 
                SET last_message_id = ?, last_checked = ?
                WHERE id = ?
            """, (message_id, datetime.now(), source_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update source: {e}")

    def add_news(self, news: News) -> int:
        """Add a new news article"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO news 
                (message_id, source_id, source_name, message_date, original_text, 
                 original_link, text_hash, normalized_text_hash, is_breaking_news, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news.message_id,
                news.source_id,
                news.source_name,
                news.message_date,
                news.original_text,
                news.original_link,
                news.text_hash,
                news.normalized_text_hash,
                news.is_breaking_news,
                datetime.now()
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            logger.debug(f"News already exists: {news.message_id}")
            return -1
        except Exception as e:
            logger.error(f"Failed to add news: {e}")
            return -1

    def is_duplicate(self, text_hash: str, normalized_hash: str) -> bool:
        """Check if news is duplicate"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM news WHERE text_hash = ? OR normalized_text_hash = ?",
                (text_hash, normalized_hash)
            )
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check duplicate: {e}")
            return False

    def mark_published(self, news_id: int):
        """Mark news as published"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                UPDATE news 
                SET published = 1, published_at = ?
                WHERE id = ?
            """, (datetime.now(), news_id))
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to mark news as published: {e}")

    def add_admin(self, user_id: int, user_name: str, permission_level: str = "ADMIN") -> bool:
        """Add an admin user"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO admins (user_id, user_name, permission_level, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_name, permission_level, datetime.now()))
            self.conn.commit()
            logger.info(f"Admin added: {user_name} ({user_id})")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Admin already exists: {user_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to add admin: {e}")
            return False

    def get_admins(self) -> List[Admin]:
        """Get all admins"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT * FROM admins")
            rows = cursor.fetchall()
            admins = []
            for row in rows:
                admins.append(Admin(
                    id=row[0],
                    user_id=row[1],
                    user_name=row[2],
                    permission_level=row[3],
                    created_at=row[4]
                ))
            return admins
        except Exception as e:
            logger.error(f"Failed to get admins: {e}")
            return []

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT id FROM admins WHERE user_id = ?", (user_id,))
            return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Failed to check admin status: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM sources WHERE enabled = 1")
            total_sources = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM news")
            total_news = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM news WHERE published = 1")
            published_news = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM error_logs")
            total_errors = cursor.fetchone()[0]

            return {
                "total_sources": total_sources,
                "total_news": total_news,
                "published_news": published_news,
                "total_errors": total_errors,
                "duplicate_count": total_news - published_news
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}

    def set_setting(self, key: str, value: str):
        """Set a setting"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now())
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to set setting: {e}")

    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.error(f"Failed to get setting: {e}")
            return None
