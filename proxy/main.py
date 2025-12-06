from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
from .config import settings
from .middleware import TimingMiddleware
from .utils import get_logger
from fastapi import FastAPI, Request, Response  # <--- Added Response

# Global HTTP Client
http_client = None

# Initialize Traffic Inspector Logger
request_logger = get_logger("traffic_inspector")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create the client
    global http_client
    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")
    yield
    # Shutdown: Close the client
    await http_client.aclose()
    print("🔓 Hunter disconnected")

app = FastAPI(
    title="Zombie API Hunter",
    description="A reverse proxy with ML-powered anomaly detection.",
    version="1.0.0",
    contact={
        "name": "Tejas Samir Alawani",  # Replace with your name if you wish
        "email": "tejas31007@gmail.com",
    },
    lifespan=lifespan
)

# ACTIVATE MIDDLEWARE
app.add_middleware(TimingMiddleware)

@app.get("/health")
async def health_check():
    """
    Explicit health check for monitoring tools.
    """
    return {"status": "Hunter is active"}
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(path_name: str, request: Request):
    global http_client
    url = f"/{path_name}"
    
    # 1. Capture Body
    body = await request.body()
    
    # 2. Log it (Safety check: decode only if it's text)
    try:
        log_body = body.decode('utf-8')[:100]
    except:
        log_body = "(Binary Data)"
        
    request_logger.info(f"Incoming -> IP: {request.client.host} | Body: {log_body}")

    try:
        # 3. Forward to Java
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=body
        )
        
        # 4. Return Raw Content (Fixes the crash)
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type")
        )
        
    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}