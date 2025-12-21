import pytest
from proxy.rate_limiter import RateLimiter

@pytest.mark.asyncio
async def test_rate_limiter_allow(mock_redis):
    # Setup: Create limiter with fake redis
    limiter = RateLimiter(mock_redis)

    # Test: If current count (1) is less than limit (5), should return True
    # We mock the pipeline result to return [1, 1] (current_count, expire_result)
    pipeline = mock_redis.pipeline.return_value
    pipeline.execute.return_value = [1, 1]

    is_allowed = await limiter.is_allowed("1.2.3.4", limit=5, window=60)

    assert is_allowed is True

@pytest.mark.asyncio
async def test_rate_limiter_block(mock_redis):
    limiter = RateLimiter(mock_redis)

    # Test: If current count (10) is greater than limit (5), should return False
    pipeline = mock_redis.pipeline.return_value
    pipeline.execute.return_value = [10, 1] # 10 requests made

    is_allowed = await limiter.is_allowed("1.2.3.4", limit=5, window=60)

    assert is_allowed is False