import redis.asyncio as redis
from .utils import get_logger

logger = get_logger("rate_limiter")

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(self, ip: str, limit: int, window: int) -> bool:
        """
        Checks if an IP has exceeded the rate limit.
        Returns: True (Allowed), False (Blocked)
        """
        if not self.redis:
            return True # Fail open if Redis is down

        key = f"rate_limit:{ip}"

        try:
            # Increment the counter
            # IF key doesn't exist, Redis creates it with value 1
            current_count = await self.redis.incr(key)

            # If this is the first request, set the expiration timer
            if current_count == 1:
                await self.redis.expire(key, window)

            # Check if limit exceeded
            if current_count > limit:
                logger.warning(f"⏳ Rate Limit Exceeded: {ip} ({current_count}/{limit})")
                return False

            return True

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True # Fail open on error

# We will initialize this in main.py