import datetime
import json
import uuid
from contextlib import asynccontextmanager
from typing import Any, Optional

import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel  # Moved to top for cleaner structure

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
    request: Request, body_str: str, action: str, risk_score: float = 0.0
) -> None:
    """Pushes a log entry to Redis with a timestamp and action tag."""
    if not redis_client:
        return

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": request.url.path,
        "headers": dict(request.headers),
        "body": body_str[:1000],
        "action": action,
        "risk_score": risk_score,
    }

    try:
        await redis_client.lpush(settings.REDIS_QUEUE_NAME, json.dumps(log_entry))  # type: ignore
    except Exception as e:
        request_logger.error(f"Failed to push to Redis: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    global http_client, redis_client, rate_limiter

    http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")

    redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    rate_limiter = RateLimiter(redis_client)
    yield
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
# 📝 FEEDBACK SYSTEM (NEW)
# =========================================================
# This must be defined BEFORE the proxy catch-all route!

class FeedbackRequest(BaseModel):
    request_id: str
    actual_label: str  # e.g., "safe", "malicious"
    comments: str = ""

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Receives user feedback on AI predictions and saves it to Redis.
    """
    if not redis_client:
        return {"status": "error", "message": "Redis not connected"}

    # Create a record of the mistake
    feedback_entry = {
        "request_id": feedback.request_id,
        "actual_label": feedback.actual_label,
        "comments": feedback.comments,
        "timestamp": datetime.datetime.now().isoformat()
    }

    # Push to a new Redis list: 'feedback_queue'
    try:
        await redis_client.lpush("feedback_queue", json.dumps(feedback_entry)) # type: ignore
        print(f"📝 Feedback saved for {feedback.request_id}")
        return {"status": "success", "message": "Feedback stored for retraining"}
    except Exception as e:
        print(f"❌ Failed to save feedback: {e}")
        return {"status": "error", "message": str(e)}


# =========================================================
# 🚦 PROXY TRAFFIC HANDLER
# =========================================================

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(path_name: str, request: Request) -> Any:
    global http_client, redis_client, rate_limiter
    url = f"/{path_name}"

    if not rate_limiter or not http_client:
        return Response("System initializing...", status_code=503)

    # 0. RATE LIMIT CHECK
    client_host = request.client.host if request.client else "unknown"

    is_allowed = await rate_limiter.is_allowed(
        client_host,
        limit=settings.RATE_LIMIT_COUNT,
        window=settings.RATE_LIMIT_WINDOW,
    )

    if not is_allowed:
        await log_request(request, "[Rate Limited]", "BLOCKED_RATE", 0.0)
        return Response(
            content='{"error": "Too Many Requests. Slow down!"}',
            status_code=429,
            media_type="application/json",
        )

    # 1. Capture Body
    body = await request.body()
    try:
        body_str = body.decode("utf-8")
    except Exception:
        body_str = "[Binary Data]"

    # 2. AI SECURITY CHECK
    prediction = ai_engine.predict(url, request.method, body_str)
    risk_score = ai_engine.get_risk_score(url, request.method, body_str)

    if prediction == -1:
        await log_request(request, body_str, "BLOCKED_AI", risk_score)

        request_id = str(uuid.uuid4())
        request_logger.warning(
            f"⛔ BLOCKED | ID: {request_id} | Score: {risk_score:.4f} | Path: {url}"
        )

        html_content = load_template(
            "blocked.html", {"client_ip": client_host, "request_id": request_id}
        )

        if html_content:
            return HTMLResponse(content=html_content, status_code=403)
        return Response(content='{"error": "Blocked"}', status_code=403)

    # 3. ALLOWED REQUEST
    await log_request(request, body_str, "ALLOWED", risk_score)

    request_logger.info(f"Forwarding -> IP: {client_host}")

    try:
        upstream_response = await http_client.request(
            method=request.method, url=url, params=request.query_params, content=body
        )

        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type"),
        )

    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}