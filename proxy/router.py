# proxy/router.py
import datetime
import json
import uuid
from typing import Any
from fastapi import APIRouter, Request, Response, Security
from fastapi.responses import HTMLResponse, JSONResponse

# Internal Modules
from . import state  # <--- Access the shared clients
from .config import settings
from .ai_engine import ai_engine
from .utils import load_template
from .security import verify_api_key
from .schemas import FeedbackRequest
from .logger import get_logger

router = APIRouter()
request_logger = get_logger("traffic_inspector")

# --- HELPER: LOGGING ---
async def log_request(request: Request, payload_text: str, action_taken: str, risk_score: float = 0.0) -> None:
    """Pushes a structured log entry to Redis Streams."""
    if not state.redis_client:
        return

    # 1. GET ID FROM MIDDLEWARE (Traceability Fix)
    # We use the same ID that was returned to the client in the headers
    req_id = getattr(request.state, "request_id", "unknown")

    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "ip": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": request.url.path,
        "headers": json.dumps(dict(request.headers)),
        "body": payload_text[:1000],
        "action": action_taken,
        "risk_score": str(risk_score),
        "request_id": req_id  # <--- NOW CONSISTENT WITH HEADERS
    }

    try:
        await state.redis_client.xadd(settings.REDIS_STREAM_NAME, log_entry)
        # Auto-Cleanup: Keep last 24 hours
        one_day_ago = int((datetime.datetime.now().timestamp() - 86400) * 1000)
        await state.redis_client.xtrim(settings.REDIS_STREAM_NAME, minid=str(one_day_ago), approximate=True)
    except Exception as e:
        request_logger.error(f"Failed to push to Redis Stream: {e}")

# --- ROUTE: HEALTH CHECK (New) ---
#/health check endpoint to verify API and Redis status
@router.get("/health")
async def health_check():
    """
    Checks if the API and Redis are running.
    """
    health_status = {"status": "ok", "redis": "connected"}
    
    # Check Redis Connection
    try:
        if state.redis_client:
            await state.redis_client.ping()
        else:
            health_status["status"] = "degraded"
            health_status["redis"] = "disconnected"
    except Exception as e:
        health_status["status"] = "error"
        health_status["redis"] = str(e)

    # Return 200 only if fully healthy
    status_code = 200 if health_status["status"] == "ok" else 503
    return JSONResponse(content=health_status, status_code=status_code)

# --- ROUTE: FEEDBACK ---
@router.post("/feedback")
async def submit_feedback(user_feedback: FeedbackRequest):
    if not state.redis_client:
        return {"status": "error", "message": "Redis not connected"}

    feedback_entry = {
        "request_id": user_feedback.request_id,
        "actual_label": user_feedback.actual_label,
        "comments": user_feedback.comments,
        "timestamp": datetime.datetime.now().isoformat()
    }

    try:
        await state.redis_client.lpush("feedback_queue", json.dumps(feedback_entry))
        request_logger.info(f"📝 Feedback saved for {user_feedback.request_id}")
        return {"status": "success", "message": "Feedback stored for retraining"}
    except Exception as e:
        request_logger.error(f"❌ Failed to save feedback: {e}")
        return {"status": "error", "message": str(e)}

# --- ROUTE: PROXY TRAFFIC HANDLER ---
@router.api_route("/{captured_path:path}", methods=["GET", "POST", "PUT", "DELETE"], dependencies=[Security(verify_api_key)])
async def proxy_request(captured_path: str, incoming_request: Request) -> Any:
    target_endpoint = f"/{captured_path}"
    req_id = getattr(incoming_request.state, "request_id", "unknown")

    if not state.rate_limiter or not state.http_client:
        return Response("System initializing...", status_code=503)

    # 0. RATE LIMIT CHECK
    client_ip = incoming_request.client.host if incoming_request.client else "unknown"
    is_allowed = await state.rate_limiter.is_allowed(
        client_ip,
        limit=settings.RATE_LIMIT_COUNT,
        window=settings.RATE_LIMIT_WINDOW,
    )

    if not is_allowed:
        await log_request(incoming_request, "[Rate Limited]", "BLOCKED_RATE", 0.0)
        return Response(content='{"error": "Too Many Requests. Slow down!"}', status_code=429, media_type="application/json")

    # 1. DATA CAPTURE
    raw_body_bytes = await incoming_request.body()
    try:
        decoded_payload = raw_body_bytes.decode("utf-8")
    except Exception:
        decoded_payload = "[Binary Data]"

    # 2. AI SECURITY CHECK
    security_verdict = ai_engine.predict(target_endpoint, incoming_request.method, decoded_payload)
    threat_probability = ai_engine.get_risk_score(target_endpoint, incoming_request.method, decoded_payload)

    if security_verdict == -1:
        await log_request(incoming_request, decoded_payload, "BLOCKED_AI", threat_probability)
        # Use the MIDDLEWARE ID for the block page so admins can trace it
        request_logger.warning(f"⛔ BLOCKED | ID: {req_id} | Score: {threat_probability:.4f} | Path: {target_endpoint}")

        html_content = load_template("blocked.html", {"client_ip": client_ip, "request_id": req_id})
        if html_content:
            return HTMLResponse(content=html_content, status_code=403)
        return Response(content='{"error": "Blocked by Zombie Hunter"}', status_code=403)

    # 3. FORWARD TO UPSTREAM
    await log_request(incoming_request, decoded_payload, "ALLOWED", threat_probability)
    request_logger.info(f"Forwarding -> IP: {client_ip}")

    try:
        upstream_response = await state.http_client.request(
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
    except Exception as exc:
        return JSONResponse(status_code=502, content={"error": f"Connection to victim failed: {str(exc)}"})