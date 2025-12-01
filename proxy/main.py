from fastapi import FastAPI

# Initialize the "Hunter" (Our Proxy Server)
app = FastAPI(
    title="Zombie API Hunter",
    description="A reverse proxy with ML-powered anomaly detection.",
    version="1.0.0"
)

@app.get("/")
async def root():
    """
    Health Check Endpoint.
    """
    return {"message": "The Hunter is active.", "status": "running"}

@app.get("/health")
async def health_check():
    """
    Explicit health check for monitoring tools.
    """
    return {"status": "ok"}