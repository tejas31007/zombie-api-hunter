import json  # <--- NEW: For converting logs to text
import redis.asyncio as redis  # <--- NEW: The async Redis driver
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
import httpx
from .config import settings
from .middleware import TimingMiddleware
from .utils import get_logger

# Global Clients
http_client = None
redis_client = None  # <--- NEW: The connection to the "Brain"

# Initialize Traffic Inspector Logger
request_logger = get_logger("traffic_inspector")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, redis_client
    
    # 1. Start HTTP Client (for forwarding traffic)
    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")
    
    # 2. Start Redis Client (for pushing logs) <--- NEW
    # We use decode_responses=True so we get strings back, not bytes
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    yield
    
    # Shutdown: Close connections
    await http_client.aclose()
    await redis_client.aclose()
    print("🔓 Hunter disconnected")

app = FastAPI(
    title="Zombie API Hunter",
    description="A reverse proxy with ML-powered anomaly detection.",
    version="1.0.0",
    contact={
        "name": "Tejas Samir Alawani",
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
    global http_client, redis_client
    url = f"/{path_name}"
    
    # 1. Capture Body
    body = await request.body()
    
    # 2. Decode Body (Safety check for binary data)
    try:
        body_str = body.decode('utf-8')
    except:
        body_str = "[Binary Data]"
        
    # 3. Prepare the Log Entry (The Data Packet) <--- NEW
    log_entry = {
        "ip": request.client.host,
        "method": request.method,
        "path": url,
        "headers": dict(request.headers),
        "body": body_str[:1000] # Truncate huge bodies to save space
    }
    
    # 4. PUSH to Redis Queue (Fire and Forget) <--- NEW
    if redis_client:
        try:
            # We push to the 'Left' of the list (Queue)
            await redis_client.lpush(settings.REDIS_QUEUE_NAME, json.dumps(log_entry))
        except Exception as e:
            request_logger.error(f"Failed to push to Redis: {e}")

    # Log to console as well (Optional, good for debugging)
    request_logger.info(f"Incoming -> IP: {request.client.host} | Body: {body_str[:100]}")

    try:
        # 5. Forward to Java Victim
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=body
        )
        
        # 6. Return Raw Content (Handles Images/JSON/Text)
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type")
        )
        
    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}