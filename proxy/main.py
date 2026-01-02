# proxy/main.py
from contextlib import asynccontextmanager
from typing import Any
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Internal Imports
from .config import settings
from .middleware import TimingMiddleware
from .rate_limiter import RateLimiter
from .router import router
from . import state  # We import state to initialize the globals

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    # 1. Initialize Clients in the shared 'state' module
    state.http_client = httpx.AsyncClient(base_url=settings.TARGET_URL)
    print(f"🔒 Hunter connected to Target: {settings.TARGET_URL}")

    state.redis_client = redis.Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )
    print(f"🧠 Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    state.rate_limiter = RateLimiter(state.redis_client)
    
    yield
    
    # 2. Cleanup
    if state.http_client:
        await state.http_client.aclose()
    if state.redis_client:
        await state.redis_client.aclose()
    print("🔓 Hunter disconnected")

app = FastAPI(
    title="Zombie API Hunter",
    description="A reverse proxy with ML-powered anomaly detection.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- MIDDLEWARE ---
app.add_middleware(TimingMiddleware)

# --- GLOBAL EXCEPTION HANDLER (Commit 4) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Zombie Error",
            "detail": str(exc),
            "path": request.url.path
        }
    )

# --- INCLUDE ROUTES ---
app.include_router(router)