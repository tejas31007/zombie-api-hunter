import json
import uuid
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import httpx
from .ai_engine import ai_engine
from .config import settings
from .middleware import TimingMiddleware
from .utils import get_logger, load_template  # <--- Updated import

# Global Clients
http_client = None
redis_client = None

request_logger = get_logger("traffic_inspector")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, redis_client
    
    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")
    
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, 
        port=settings.REDIS_PORT, 
        decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    yield
    
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

app.add_middleware(TimingMiddleware)

@app.get("/health")
async def health_check():
    return {"status": "Hunter is active"}

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(path_name: str, request: Request):
    global http_client, redis_client
    url = f"/{path_name}"
    
    body = await request.body()
    try:
        body_str = body.decode('utf-8')
    except:
        body_str = "[Binary Data]"

    # =========================================================
    # 🧠 AI SECURITY CHECK
    # =========================================================
    prediction = ai_engine.predict(url, request.method, body_str)
    
    if prediction == -1:
        # 1. Generate Forensics Data
        request_id = str(uuid.uuid4())
        client_ip = request.client.host
        
        # 2. Get Score
        risk_score = ai_engine.get_risk_score(url, request.method, body_str)
        request_logger.warning(f"⛔ BLOCKED | ID: {request_id} | Score: {risk_score:.4f} | Path: {url}")
        
        # 3. Load HTML Template
        html_content = load_template("blocked.html", {
            "client_ip": client_ip,
            "request_id": request_id
        })
        
        if html_content:
            return HTMLResponse(content=html_content, status_code=403)
        else:
            # Fallback if HTML is missing
            return Response(
                content='{"error": "Request blocked by AI Security Hunter"}',
                status_code=403,
                media_type="application/json"
            )
    # =========================================================
        
    log_entry = {
        "ip": request.client.host,
        "method": request.method,
        "path": url,
        "headers": dict(request.headers),
        "body": body_str[:1000] 
    }
    
    if redis_client:
        try:
            await redis_client.lpush(settings.REDIS_QUEUE_NAME, json.dumps(log_entry))
        except Exception as e:
            request_logger.error(f"Failed to push to Redis: {e}")

    request_logger.info(f"Incoming -> IP: {request.client.host} | Body: {body_str[:100]}")

    try:
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            params=request.query_params,
            content=body
        )
        
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type")
        )
        
    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}