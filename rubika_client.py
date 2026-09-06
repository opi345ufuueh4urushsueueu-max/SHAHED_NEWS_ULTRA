"""
SHAHED NEWS ULTRA - Rubika Client
"""

import asyncio
from typing import Optional, List, Dict, Any
from logger import logger
from retry import RetryEngine

try:
    from rubpy import Client
    from rubpy.types import User, Chat, Message
except ImportError:
    logger.error("rubpy library not installed. Install with: pip install rubpy")
    Client = None


class RubikaClient:
    """Rubika messaging client wrapper"""

    def __init__(self, phone: str, password: str):
        self.phone = phone
        self.password = password
        self.client = None
        self.connected = False
        self.retry_engine = RetryEngine()

    async def connect(self) -> bool:
        """Connect to Rubika"""
        try:
            if not Client:
                logger.error("rubpy library not available")
                return False

            logger.info(f"Connecting to Rubika as {self.phone}...")

            self.client = Client()

            # Set up event handlers
            self.client.on_message_recv()(self._handle_message)

            # Connect
            await self.client.connect()
            logger.info("Connected to Rubika")

            # Authenticate
            result = await self.retry_engine.execute_async(
                self._authenticate
            )

            if result:
                self.connected = True
                logger.info("✓ Rubika authentication successful")
                return True
            else:
                logger.error("✗ Rubika authentication failed")
                return False

        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            self.connected = False
            return False

    async def _authenticate(self) -> bool:
        """Authenticate with phone and password"""
        try:
            await self.client.auth.send_code(self.phone)
            logger.info("Code sent to phone")

            # In real implementation, get OTP from user
            # For now, we'll assume it's provided via environment or input
            otp = input("Enter OTP: ")

            await self.client.auth.authenticate(
                phone_number=self.phone,
                password=self.password,
                verification_code=otp
            )

            return True
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False

    async def disconnect(self):
        """Disconnect from Rubika"""
        if self.client:
            await self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from Rubika")

    async def get_channel_messages(
        self,
        channel_id: int,
        limit: int = 10,
        from_message_id: int = 0
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel"""
        try:
            if not self.connected:
                logger.warning("Not connected to Rubika")
                return []

            messages = await self.retry_engine.execute_async(
                self.client.get_channel_messages,
                channel_id,
                limit,
                from_message_id
            )

            if messages:
                result = []
                for msg in messages:
                    result.append({
                        "message_id": msg.message_id,
                        "text": msg.text if hasattr(msg, "text") else "",
                        "channel_id": channel_id,
                        "date": msg.date if hasattr(msg, "date") else None,
                        "link": msg.link if hasattr(msg, "link") else None,
                    })
                return result
            return []

        except Exception as e:
            logger.error(f"Failed to get messages: {str(e)}")
            return []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[int]:
        """Send message to chat/channel"""
        try:
            if not self.connected:
                logger.warning("Not connected to Rubika")
                return None

            message = await self.retry_engine.execute_async(
                self.client.send_message,
                chat_id,
                text,
                reply_to_message_id
            )

            if message:
                logger.debug(f"Message sent: {message.message_id}")
                return message.message_id
            return None

        except Exception as e:
            logger.error(f"Failed to send message: {str(e)}")
            return None

    async def get_channel_info(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get channel information"""
        try:
            if not self.connected:
                logger.warning("Not connected to Rubika")
                return None

            channel = await self.retry_engine.execute_async(
                self.client.get_channel,
                channel_id
            )

            if channel:
                return {
                    "id": channel.channel_id,
                    "name": channel.name,
                    "username": channel.username,
                    "about": getattr(channel, "about", ""),
                    "members_count": getattr(channel, "members_count", 0),
                }
            return None

        except Exception as e:
            logger.error(f"Failed to get channel info: {str(e)}")
            return None

    async def is_connected(self) -> bool:
        """Check if connected"""
        if not self.connected:
            return False

        try:
            # Try a simple check
            return await self.retry_engine.check_connection(
                lambda: asyncio.sleep(0)
            )
        except Exception:
            return False

    async def _handle_message(self, message):
        """Handle incoming messages"""
        try:
            logger.debug(f"Message received: {message.message_id}")
            # This would be used for real-time updates
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
