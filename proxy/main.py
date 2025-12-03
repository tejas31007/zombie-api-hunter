from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import httpx
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