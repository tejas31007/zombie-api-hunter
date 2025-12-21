import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
# --- Add these imports at the top if missing ---
from unittest.mock import patch
# We import 'app' from main. If main.py doesn't exist yet, this will error (we fix that next).
from main import app

# We will import the actual app later when we verify main.py exists
# from main import app 

# --- MOCK CLASSES ---
# These simulate the dependencies so we can test the Proxy logic 
# without needing a real Redis server or AI Engine running.

@pytest.fixture
def mock_redis():
    """Simulates Redis for Rate Limiting tests"""
    mock = MagicMock()
    # By default, allow everything (incr returns 1)
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def mock_ai_engine():
    """Simulates the AI Engine for Security tests"""
    mock = MagicMock()
    # By default, return 0.0 (Safe)
    mock.predict_threat_score = AsyncMock(return_value=0.0)
    return mock


@pytest.mark.asyncio
async def test_block_sql_injection():
    """
    Test 1: Security Block
    Scenario: AI detects high threat score (0.85).
    Expected: Proxy returns 403 Forbidden.
    """
    # SETUP: We Mock the AI Engine to force it to say "This is Dangerous" (Score 0.85)
    # The path 'proxy.ai_engine.AIEngine.predict_threat_score' must match where your class is.
    with patch("proxy.ai_engine.AIEngine.predict_threat_score", return_value=0.85):
        
        # ACT: Use httpx to send a request to our app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Send a fake SQL Injection payload
            response = await client.get("/user?query=' OR 1=1")
            
            # ASSERT: Verify the Block
            assert response.status_code == 403
            # Optional: Check the error message (adjust based on your actual error message)
            assert "blocked" in response.text.lower()

# --- SETUP COMPLETED ---
# We are ready to write the actual tests in the next commits.