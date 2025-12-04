from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
from .config import settings
from .middleware import TimingMiddleware
from .config import settings

# Global HTTP Client
http_client = None

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
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "Hunter is active"}

@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_request(path_name: str, request: Request):
    """
    Catches all traffic, forwards it to the Victim, and returns the response.
    """
    global http_client

    # 1. Forward the request to the Victim (Async!)
    # We strip the original host header to avoid confusion
    url = f"/{path_name}"

    try:
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            # specific query params (?)
            params=request.query_params, 
            # headers (optional, usually requires filtering)
            # content=await request.body()
        )

        # 2. Return the Victim's response to the User
        return upstream_response.json()

    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}