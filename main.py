"""
SHAHED NEWS ULTRA - Main Application
"""

import asyncio
import signal
from datetime import datetime
from typing import Optional
from logger import logger
from config import (
    RUBIKA_PHONE,
    RUBIKA_PASSWORD,
    DESTINATION_CHANNEL_ID,
    OWNER_ID,
    POLL_INTERVAL,
    SEND_STARTUP_MESSAGE,
    STARTUP_MESSAGE_COOLDOWN,
)
from database import Database
from rubika_client import RubikaClient
from processor import TextProcessor
from duplicate_detector import DuplicateDetector
from models import Source, News, SystemState
import json
from pathlib import Path


class ShahedNewsUltra:
    """Main application class"""

    def __init__(self):
        self.db = Database()
        self.rubika = RubikaClient(RUBIKA_PHONE, RUBIKA_PASSWORD)
        self.state = SystemState()
        self.running = False
        self.last_startup_message_time = 0

    async def startup(self):
        """Initialize and start the system"""
        try:
            logger.info("🚀 SHAHED NEWS ULTRA STARTING...")
            self._print_banner()

            # Connect to Rubika
            logger.info("[1/5] Connecting to Rubika...")
            if not await self.rubika.connect():
                logger.error("Failed to connect to Rubika")
                return False

            # Check destination
            logger.info("[2/5] Checking destination channel...")
            dest_info = await self.rubika.get_channel_info(DESTINATION_CHANNEL_ID)
            if not dest_info:
                logger.error("Destination channel not accessible")
                return False

            logger.info(f"✓ Destination: {dest_info['name']}")

            # Load sources
            logger.info("[3/5] Loading sources...")
            sources = self.db.get_sources(enabled_only=True)
            logger.info(f"✓ Loaded {len(sources)} sources")

            # Start message
            if SEND_STARTUP_MESSAGE:
                await self._send_startup_message()

            self.running = True
            self.state.last_startup = datetime.now()
            logger.info("[4/5] System ready")
            logger.info("[5/5] Starting monitor...")

            return True

        except Exception as e:
            logger.error(f"Startup failed: {str(e)}")
            return False

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("\n🛑 Shutdown requested...")
        self.running = False

        logger.info("⏳ Stopping operations...")
        await asyncio.sleep(1)

        logger.info("⏳ Closing Rubika connection...")
        await self.rubika.disconnect()

        logger.info("⏳ Closing database...")
        self.db.close()

        logger.info("✅ SHAHED NEWS ULTRA stopped safely.")

    async def collect_news(self):
        """Collect news from sources"""
        while self.running:
            try:
                sources = self.db.get_sources(enabled_only=True)

                for source in sources:
                    try:
                        logger.debug(f"Checking source: {source.channel_username}")

                        messages = await self.rubika.get_channel_messages(
                            source.channel_id,
                            limit=5,
                            from_message_id=source.last_message_id or 0
                        )

                        for msg in messages:
                            # Check if duplicate
                            text_hash, norm_hash = DuplicateDetector.calculate_hashes(msg["text"])

                            if self.db.is_duplicate(text_hash, norm_hash):
                                logger.debug(f"Duplicate detected: {source.channel_username}")
                                self.state.duplicate_count += 1
                                continue

                            # Validate text
                            if not TextProcessor.validate_text(msg["text"]):
                                logger.debug("Text validation failed")
                                continue

                            # Add to database
                            news = News(
                                id=0,
                                message_id=msg["message_id"],
                                source_id=source.id,
                                source_name=source.channel_name,
                                message_date=msg["date"],
                                original_text=msg["text"],
                                original_link=msg["link"],
                                text_hash=text_hash,
                                normalized_text_hash=norm_hash,
                                is_breaking_news=DuplicateDetector.detect_breaking_news(msg["text"]),
                            )

                            news_id = self.db.add_news(news)
                            if news_id > 0:
                                logger.info(f"✓ News added: {source.channel_name}")
                                self.state.total_news_received += 1

                        # Update last message
                        if messages:
                            self.db.update_source_last_message(
                                source.id,
                                messages[-1]["message_id"]
                            )

                    except Exception as e:
                        logger.error(f"Error processing source {source.channel_username}: {str(e)}")
                        self.state.error_count += 1
                        continue

                await asyncio.sleep(POLL_INTERVAL)

            except Exception as e:
                logger.error(f"Collection error: {str(e)}")
                self.state.error_count += 1
                await asyncio.sleep(POLL_INTERVAL)

    async def publish_news(self):
        """Publish collected news"""
        while self.running:
            try:
                # Get unpublished news
                cursor = self.db.conn.cursor()
                cursor.execute(
                    "SELECT id, source_name, original_text, original_link, is_breaking_news "
                    "FROM news WHERE published = 0 LIMIT 1"
                )
                row = cursor.fetchone()

                if not row:
                    await asyncio.sleep(5)
                    continue

                news_id, source_name, text, link, is_breaking = row

                # Format for publishing
                formatted_parts = TextProcessor.format_for_publishing(
                    source_name,
                    text,
                    link,
                    bool(is_breaking)
                )

                # Send to destination
                success = True
                for part in formatted_parts:
                    msg_id = await self.rubika.send_message(
                        DESTINATION_CHANNEL_ID,
                        part
                    )
                    if not msg_id:
                        success = False
                        break

                if success:
                    self.db.mark_published(news_id)
                    self.state.total_news_published += 1
                    logger.info(f"✓ News published: {source_name}")
                else:
                    logger.warning("Failed to publish news, will retry")
                    await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Publishing error: {str(e)}")
                self.state.error_count += 1
                await asyncio.sleep(10)

    async def health_monitor(self):
        """Monitor system health"""
        while self.running:
            try:
                # Check connection
                connected = await self.rubika.is_connected()
                self.state.connection_status = "CONNECTED" if connected else "DISCONNECTED"

                # Log stats
                stats = self.db.get_stats()
                logger.debug(f"Stats: {json.dumps(stats, indent=2)}")

                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"Health monitor error: {str(e)}")
                await asyncio.sleep(60)

    async def run(self):
        """Main run loop"""
        if not await self.startup():
            return

        try:
            # Run all tasks concurrently
            await asyncio.gather(
                self.collect_news(),
                self.publish_news(),
                self.health_monitor(),
            )

        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
        finally:
            await self.shutdown()

    def _print_banner(self):
        """Print startup banner"""
        banner = """
╔══════════════════════════════════════════════╗
║                                              ║
║          📡 SHAHED NEWS ULTRA               ║
║                                              ║
║       ⚡ INTELLIGENT NEWS SYSTEM ⚡          ║
║                                              ║
╚══════════════════════════════════════════════╝

🚀 SYSTEM INITIALIZING...
        """
        print(banner)

    async def _send_startup_message(self):
        """Send startup message to destination"""
        try:
            now = datetime.now().timestamp()
            if now - self.last_startup_message_time < STARTUP_MESSAGE_COOLDOWN:
                logger.debug("Startup message cooldown active")
                return

            message = """🔴 سیستم شاهد نیوز آنلاین شد

📡 سیستم خبری هوشمند روبیکا فعال است.

✅ وضعیت: آنلاین
📚 منابع: در حال بارگذاری...
🔄 مانیتور: فعال

برای اطلاعات بیشتر /وضعیت را وارد کنید."""

            await self.rubika.send_message(DESTINATION_CHANNEL_ID, message)
            self.last_startup_message_time = now
            logger.info("Startup message sent")

        except Exception as e:
            logger.error(f"Failed to send startup message: {str(e)}")


async def main():
    """Main entry point"""
    app = ShahedNewsUltra()

    def signal_handler(sig, frame):
        logger.info("Signal handler called")
        asyncio.create_task(app.shutdown())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
