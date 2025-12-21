import pytest
from proxy.rate_limiter import RateLimiter

# --- FAKE CLASSES (Simulate Redis) ---
class FakePipeline:
    def __init__(self, execute_result):
        self.execute_result = execute_result

    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc_val, exc_tb): pass
    async def incr(self, *args, **kwargs): pass
    async def expire(self, *args, **kwargs): pass
    async def execute(self): return self.execute_result

class FakeRedis:
    def __init__(self, execute_result):
        self.execute_result = execute_result

    def pipeline(self, transaction=True, shard_hint=None):
        return FakePipeline(self.execute_result)
    
    async def incr(self, *args, **kwargs): return 1
    async def expire(self, *args, **kwargs): return 1

# --- TESTS ---

@pytest.mark.asyncio
async def test_rate_limiter_allow():
    # SETUP: Fake Redis returns [1, 1] (Count=1)
    fake_redis = FakeRedis(execute_result=[1, 1])
    limiter = RateLimiter(fake_redis) # type: ignore
    
    # TEST: Count (1) < Limit (5) -> Should be Allowed (True)
    is_allowed = await limiter.is_allowed("1.2.3.4", limit=5, window=60)
    assert is_allowed is True

@pytest.mark.asyncio
async def test_rate_limiter_block():
    # SETUP: Fake Redis returns [10, 1] (Count=10)
    fake_redis = FakeRedis(execute_result=[10, 1])
    limiter = RateLimiter(fake_redis) # type: ignore
    
    # TEST: Count (10) > Limit (5) -> Should be Blocked (False)
    is_allowed = await limiter.is_allowed("1.2.3.4", limit=5, window=60)
    assert is_allowed is False