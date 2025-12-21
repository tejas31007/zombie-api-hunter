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
            return True  # Fail open if Redis is down

        key = f"rate_limit:{ip}"

        try:
            # OPTIMIZATION: Use a pipeline to send commands together.
            # This matches your Test setup which returns a list [count, success]
            async with self.redis.pipeline(transaction=True) as pipe:
                await pipe.incr(key)             # Increment
                await pipe.expire(key, window)   # Set expiration
                result = await pipe.execute()    # Execute block

            # result comes back as a list, e.g., [10, 1]
            current_count = result[0]

            # Check if limit exceeded
            if current_count > limit:
                logger.warning(
                    f"⏳ Rate Limit Exceeded: {ip} ({current_count}/{limit})"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Fail open on error