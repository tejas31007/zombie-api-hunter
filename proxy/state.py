# proxy/state.py
from typing import Optional
import httpx
import redis.asyncio as redis
from .rate_limiter import RateLimiter

# Shared Global State
http_client: Optional[httpx.AsyncClient] = None
redis_client: Optional[redis.Redis] = None
rate_limiter: Optional[RateLimiter] = None