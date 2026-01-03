from contextlib import asynccontextmanager
from typing import Any
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException # <--- NEW IMPORT

# Internal Imports
from .config import settings
from .middleware import TimingMiddleware
from .rate_limiter import RateLimiter
from .router import router
from . import state

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    state.http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")

    state.redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    state.rate_limiter = RateLimiter(state.redis_client)
    yield
    if state.http_client: await state.http_client.aclose()
    if state.redis_client: await state.redis_client.aclose()
    print("🔓 Hunter disconnected")

app = FastAPI(title="Zombie API Hunter", lifespan=lifespan)
app.add_middleware(TimingMiddleware)

# --- 1. CUSTOM 404 HANDLER (Client Errors) ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Catches 404 Not Found, 405 Method Not Allowed, etc.
    Returns clean JSON instead of default text.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )

# --- 2. GLOBAL 500 HANDLER (Server Crashes) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled crashes (bugs) and hides the stack trace from the user.
    """
    print(f"💥 CRITICAL ERROR: {exc}") # Log it for us
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "message": "Internal System Error",
            "path": request.url.path
        }
    )

app.include_router(router)