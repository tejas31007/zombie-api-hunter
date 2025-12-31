import datetime
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional
from fastapi import Security # Add to existing fastapi import
from .security import verify_api_key # <--- NEW IMPORT

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .ai_engine import ai_engine
from .config import settings
from .middleware import TimingMiddleware
from .rate_limiter import RateLimiter
from .utils import get_logger, load_template

request_logger = get_logger("traffic_inspector")

# --- GLOBAL CLIENTS ---
http_client: Optional[httpx.AsyncClient] = None
redis_client: Optional[redis.Redis] = None
rate_limiter: Optional[RateLimiter] = None


async def log_request(
    request: Request, payload_text: str, action_taken: str, risk_score: float = 0.0
) -> None:
    """
    Pushes a structured log entry to Redis Streams and auto-trims old logs.
    """
    if not redis_client:
        return

    # Prepare data for Stream (Must be flat key-value pairs)
    # We dump complex objects (like headers) to strings
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": request.url.path,
        "headers": json.dumps(dict(request.headers)), # Flattened for Streams
        "body": payload_text[:1000], 
        "action": action_taken,       
        "risk_score": str(risk_score), # Streams store strings best
        "request_id": str(uuid.uuid4())
    }

    try:
        # 1. Write to Stream (Commit 2)
        await redis_client.xadd(settings.REDIS_STREAM_NAME, log_entry)
        
        # 2. Auto-Cleanup: Delete logs older than 24 hours (Commit 4)
        # Calculate timestamp for 24 hours ago in milliseconds
        one_day_ago = int((datetime.datetime.now().timestamp() - 86400) * 1000)
        
        # Trim the stream to only keep IDs greater than 'one_day_ago'
        await redis_client.xtrim(settings.REDIS_STREAM_NAME, minid=str(one_day_ago), approximate=True)
        
    except Exception as e:
        request_logger.error(f"Failed to push to Redis Stream: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global http_client, redis_client, rate_limiter

    # Initialize HTTP Client for talking to the Victim API
    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")

    # Initialize Redis for Logs and Rate Limiting
    redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    rate_limiter = RateLimiter(redis_client)
    
    yield
    
    # Cleanup
    if http_client:
        await http_client.aclose()
    if redis_client:
        await redis_client.aclose()
    print("🔓 Hunter disconnected")


app = FastAPI(
    title="Zombie API Hunter",
    description="A reverse proxy with ML-powered anomaly detection.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(TimingMiddleware)


# =========================================================
# 📝 FEEDBACK SYSTEM
# =========================================================

class FeedbackRequest(BaseModel):
    request_id: str
    actual_label: str  # e.g., "safe", "malicious"
    comments: str = ""

@app.post("/feedback")
async def submit_feedback(user_feedback: FeedbackRequest):
    """
    Receives user feedback on AI predictions (False Positives/Negatives).
    """
    if not redis_client:
        return {"status": "error", "message": "Redis not connected"}

    feedback_entry = {
        "request_id": user_feedback.request_id,
        "actual_label": user_feedback.actual_label,
        "comments": user_feedback.comments,
        "timestamp": datetime.datetime.now().isoformat()
    }

    try:
        # Feedback queue can remain a List for now (simpler to process in batch)
        await redis_client.lpush("feedback_queue", json.dumps(feedback_entry))
        print(f"📝 Feedback saved for {user_feedback.request_id}")
        return {"status": "success", "message": "Feedback stored for retraining"}
    except Exception as e:
        print(f"❌ Failed to save feedback: {e}")
        return {"status": "error", "message": str(e)}


# =========================================================
# 🚦 PROXY TRAFFIC HANDLER
# =========================================================
@app.api_route("/{captured_path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Security(verify_api_key)])
async def proxy_request(captured_path: str, incoming_request: Request) -> Any:
    """
    Main pipeline: Intercept -> Rate Limit -> AI Scan -> Forward/Block
    """
    global http_client, redis_client, rate_limiter
    
    target_endpoint = f"/{captured_path}"

    if not rate_limiter or not http_client:
        return Response("System initializing...", status_code=503)

    # ---------------------------------------------------------
    # 0. RATE LIMIT CHECK
    # ---------------------------------------------------------
    client_ip = incoming_request.client.host if incoming_request.client else "unknown"

    is_allowed = await rate_limiter.is_allowed(
        client_ip,
        limit=settings.RATE_LIMIT_COUNT,
        window=settings.RATE_LIMIT_WINDOW,
    )

    if not is_allowed:
        await log_request(incoming_request, "[Rate Limited]", "BLOCKED_RATE", 0.0)
        return Response(
            content='{"error": "Too Many Requests. Slow down!"}',
            status_code=429,
            media_type="application/json",
        )

    # ---------------------------------------------------------
    # 1. DATA CAPTURE
    # ---------------------------------------------------------
    raw_body_bytes = await incoming_request.body()
    try:
        decoded_payload = raw_body_bytes.decode("utf-8")
    except Exception:
        decoded_payload = "[Binary Data]"

    # ---------------------------------------------------------
    # 2. AI SECURITY CHECK
    # ---------------------------------------------------------
    # Prediction: 1 = Allow, -1 = Block
    security_verdict = ai_engine.predict(target_endpoint, incoming_request.method, decoded_payload)
    threat_probability = ai_engine.get_risk_score(target_endpoint, incoming_request.method, decoded_payload)

    if security_verdict == -1:
        # LOG AND BLOCK
        await log_request(incoming_request, decoded_payload, "BLOCKED_AI", threat_probability)

        block_id = str(uuid.uuid4())
        request_logger.warning(
            f"⛔ BLOCKED | ID: {block_id} | Score: {threat_probability:.4f} | Path: {target_endpoint}"
        )

        html_content = load_template(
            "blocked.html", {"client_ip": client_ip, "request_id": block_id}
        )

        if html_content:
            return HTMLResponse(content=html_content, status_code=403)
        return Response(content='{"error": "Blocked by Zombie Hunter"}', status_code=403)

    # ---------------------------------------------------------
    # 3. FORWARD TO UPSTREAM (VICTIM API)
    # ---------------------------------------------------------
    await log_request(incoming_request, decoded_payload, "ALLOWED", threat_probability)

    request_logger.info(f"Forwarding -> IP: {client_ip}")

    try:
        upstream_response = await http_client.request(
            method=incoming_request.method, 
            url=target_endpoint, 
            params=incoming_request.query_params, 
            content=raw_body_bytes
        )

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type"),
        )

    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}