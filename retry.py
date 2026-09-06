"""
SHAHED NEWS ULTRA - Retry Engine
"""

import asyncio
import time
from typing import Callable, Any, Optional
from logger import logger


class RetryEngine:
    """Retry mechanism with exponential backoff"""

    def __init__(
        self,
        max_retries: int = 5,
        initial_backoff: int = 2,
        backoff_multiplier: int = 2,
        max_backoff: int = 300
    ):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff

    async def execute_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Execute function with async retry"""
        attempt = 0
        backoff = self.initial_backoff

        while attempt < self.max_retries:
            try:
                logger.debug(f"Executing {func.__name__} (attempt {attempt + 1}/{self.max_retries})")
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                attempt += 1

                if attempt >= self.max_retries:
                    logger.error(f"Max retries reached for {func.__name__}: {str(e)}")
                    return None

                logger.warning(
                    f"Attempt {attempt} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {backoff}s..."
                )

                await asyncio.sleep(backoff)
                backoff = min(backoff * self.backoff_multiplier, self.max_backoff)

        return None

    def execute_sync(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Execute function with sync retry"""
        attempt = 0
        backoff = self.initial_backoff

        while attempt < self.max_retries:
            try:
                logger.debug(f"Executing {func.__name__} (attempt {attempt + 1}/{self.max_retries})")
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                attempt += 1

                if attempt >= self.max_retries:
                    logger.error(f"Max retries reached for {func.__name__}: {str(e)}")
                    return None

                logger.warning(
                    f"Attempt {attempt} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {backoff}s..."
                )

                time.sleep(backoff)
                backoff = min(backoff * self.backoff_multiplier, self.max_backoff)

        return None

    async def check_connection(
        self,
        check_func: Callable,
        timeout: int = 5
    ) -> bool:
        """Check connection with retry"""
        try:
            result = await asyncio.wait_for(check_func(), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.warning("Connection check timed out")
            return False
        except Exception as e:
            logger.warning(f"Connection check failed: {str(e)}")
            return False
