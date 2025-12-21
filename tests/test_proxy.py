import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock, patch
from proxy.main import app

# --- FIXTURE ---
@pytest.fixture
def mock_dependencies():
    """
    Mocks the GLOBAL variables in proxy.main (http_client, rate_limiter, etc.)
    so the app thinks it is fully connected and initialized.
    """
    # 1. Create Mocks
    mock_ai = MagicMock()
    mock_ai.predict = MagicMock(return_value=1) # Default: 1 (Safe)
    mock_ai.get_risk_score = MagicMock(return_value=0.0)

    mock_limiter = MagicMock()
    mock_limiter.is_allowed = AsyncMock(return_value=True) # Default: Allowed

    mock_http = AsyncMock() # Mock the HTTP Client

    # 2. Patch the GLOBAL variables in proxy.main
    with patch("proxy.main.ai_engine", mock_ai), \
         patch("proxy.main.rate_limiter", mock_limiter), \
         patch("proxy.main.http_client", mock_http), \
         patch("proxy.main.settings") as mock_settings:
        
        # Configure Mock Settings
        mock_settings.TARGET_URL = "http://mock-target"
        mock_settings.RATE_LIMIT_COUNT = 5
        mock_settings.RATE_LIMIT_WINDOW = 60
        mock_settings.REDIS_QUEUE_NAME = "traffic_log"
        
        yield {
            "ai": mock_ai,
            "limiter": mock_limiter,
            "http": mock_http,
            "settings": mock_settings
        }

# --- TESTS ---

@pytest.mark.asyncio
async def test_block_sql_injection(mock_dependencies):
    """
    Test: Security Block
    Scenario: AI predicts -1 (Anomaly)
    Expected: 403 Forbidden
    """
    # 1. Force AI to say "Anomaly" (-1)
    mock_dependencies["ai"].predict.return_value = -1 
    mock_dependencies["ai"].get_risk_score.return_value = 0.95

    # 2. Run Request
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # We send a request that looks like an attack
        response = await client.get("/user?query=' OR 1=1")
        
        # 3. Verify Block
        assert response.status_code == 403
        assert "blocked" in response.text.lower()

@pytest.mark.asyncio
async def test_allow_normal_traffic(mock_dependencies):
    """
    Test: Normal Traffic
    Scenario: AI predicts 1 (Safe)
    Expected: 200 OK (simulated by mocking the upstream call)
    """
    # 1. Force AI to say "Safe" (1)
    mock_dependencies["ai"].predict.return_value = 1
    
    # 2. Configure the mock HTTP client to return a success response
    mock_upstream_response = MagicMock()
    mock_upstream_response.status_code = 200
    mock_upstream_response.content = b'{"data": "success"}'
    mock_upstream_response.headers = {"content-type": "application/json"}
    
    # When app calls http_client.request, return our mock response
    mock_dependencies["http"].request.return_value = mock_upstream_response

    # 3. Run Request
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/dashboard")
        
        # 4. Verify Allowed
        assert response.status_code == 200
        assert response.json() == {"data": "success"}

@pytest.mark.asyncio
async def test_rate_limit_exceeded(mock_dependencies):
    """
    Test: Rate Limiting
    Scenario: RateLimiter returns False (Limit exceeded)
    Expected: 429 Too Many Requests
    """
    # 1. Force RateLimiter to say "NOT Allowed"
    # We access the mock limiter we created in the fixture
    mock_dependencies["limiter"].is_allowed.return_value = False

    # 2. Run Request
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/fast-request")
        
        # 3. Verify Rate Limit Block
        assert response.status_code == 429
        assert "Too Many Requests" in response.text