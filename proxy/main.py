from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
from .config import settings
from .middleware import TimingMiddleware
from .utils import get_logger

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
    """
    Catches all traffic, inspects the body, forwards it to the Victim, 
    and returns the response.
    """
    global http_client
    
    url = f"/{path_name}"
    
    # 1. Capture the Body (The Payload)
    # We read the body to inspect it for malicious patterns
    body = await request.body()
    
    # 2. Log the Traffic (This is what we will feed to the AI later)
    # We slice [:100] to avoid flooding logs with huge files in the console
    request_logger.info(
        f"Incoming -> IP: {request.client.host} | Body: {body.decode('utf-8')[:100]}"
    )

    try:
        # 3. Forward the request to the Victim
        upstream_response = await http_client.request(
            method=request.method,
            url=url,
            # Pass specific query params (e.g. ?id=1)
            params=request.query_params, 
            # Pass the body we captured
            content=body
        )
        
        # 4. Return the Victim's response to the User
        return upstream_response.json()
        
    except httpx.RequestError as exc:
        return {"error": f"Connection to victim failed: {str(exc)}"}