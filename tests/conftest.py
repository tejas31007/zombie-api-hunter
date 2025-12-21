import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_redis():
    """
    Creates a fake Redis client that doesn't talk to a real database.
    """
    mock = AsyncMock()
    
    # 1. Create the pipeline object
    pipeline = MagicMock()
    
    # 2. Make it an "Async Context Manager"
    # This means when code does 'async with pipeline:', it returns the pipeline itself.
    pipeline.__aenter__.return_value = pipeline
    pipeline.__aexit__.return_value = None
    
    # 3. Default behavior for execute (Success: count=1)
    pipeline.execute = AsyncMock(return_value=[1, 1])
    
    # 4. Connect it to redis.pipeline()
    mock.pipeline.return_value = pipeline
    
    return mock