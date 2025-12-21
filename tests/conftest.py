import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_redis():
    """
    Creates a fake Redis client that doesn't talk to a real database.
    """
    mock = AsyncMock()
    # When we ask for a pipeline, return a MagicMock (sync) that returns the AsyncMock
    pipeline = MagicMock()
    pipeline.execute = AsyncMock(return_value=[1, 1]) # Default success response
    mock.pipeline.return_value = pipeline
    return mock