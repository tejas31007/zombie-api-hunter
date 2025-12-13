import json
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
import httpx
from .ai_engine import ai_engine  # <--- NEW: Import the Brain
from .config import settings
from .middleware import TimingMiddleware
from .utils import get_logger
import uuid  # <--- NEW
from fastapi.responses import HTMLResponse # <--- NEW

# Global Clients
http_client = None
redis_client = None

# Initialize Traffic Inspector Logger
request_logger = get_logger("traffic_inspector")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, redis_client
    
    # 1. Start HTTP Client (for forwarding traffic)
    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")
    
    # 2. Start Redis Client (for pushing logs)
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

    # =========================================================
    # 🧠 AI SECURITY CHECK (Phase 3 Integration)
    # =========================================================
    # We ask the brain: "Is this safe?"
    # ... inside proxy_request function ...

    # 🧠 AI SECURITY CHECK
    prediction = ai_engine.predict(url, request.method, body_str)
    
    if prediction == -1:
        # NEW: Get the raw score for observability
        risk_score = ai_engine.get_risk_score(url, request.method, body_str)
        
        # Log with the Score!
        request_logger.warning(f"⛔ AI BLOCKED | Score: {risk_score:.4f} | IP: {request.client.host} | Path: {url}")
        
        return Response(
            content='{"error": "Request blocked by AI Security Hunter"}',
            status_code=403,
            media_type="application/json"
        )
    # =========================================================


    if prediction == -1:
    # Generate a unique ID for this event (Forensics)
    request_id = str(uuid.uuid4())
    client_ip = request.client.host

    # Get the Score
    risk_score = ai_engine.get_risk_score(url, request.method, body_str)

    request_logger.warning(f"⛔ BLOCKED | ID: {request_id} | Score: {risk_score:.4f} | Path: {url}")

    # Load the HTML Template
    try:
        with open("proxy/templates/blocked.html", "r") as f:
            html_content = f.read()

        # Inject Variables (Simple Search & Replace)
        html_content = html_content.replace("{{client_ip}}", client_ip)
        html_content = html_content.replace("{{request_id}}", request_id)

        return HTMLResponse(content=html_content, status_code=403)

    except FileNotFoundError:
        # Fallback if HTML is missing
        return Response(content='{"error": "Blocked"}', status_code=403)
        
    # 3. Prepare the Log Entry (Only log if it wasn't blocked)
    log_entry = {
        "ip": request.client.host,
        "method": request.method,
        "path": url,
        "headers": dict(request.headers),
        "body": body_str[:1000] 
    }
    
    # 4. PUSH to Redis Queue
    if redis_client:
        try:
            await redis_client.lpush(settings.REDIS_QUEUE_NAME, json.dumps(log_entry))
        except Exception as e:
            request_logger.error(f"Failed to push to Redis: {e}")

    # Log to console
    request_logger.info(f"Incoming -> IP: {request.client.host} | Body: {body_str[:100]}")

    try:
        # 5. Forward to Java Victim
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=body
        )
        
        # 6. Return Raw Content
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type")
        )
        
    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}