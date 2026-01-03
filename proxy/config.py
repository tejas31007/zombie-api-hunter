import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Security
    # We use a fixed key by default so your manual tests always work.
    # In production, you would pass this via an Environment Variable.
    PROXY_API_KEY: str = os.getenv("PROXY_API_KEY", "5wVbPZsMt1jI6qYNiYxtbyE-S2VkyFyA530Au4XNwUA")
    
    # Target (The Victim)
    # Docker will inject the real target URL here
    TARGET_URL: str = os.getenv("TARGET_URL", "http://example.com")
    
    # Redis (The Brain)
    # Default to localhost for manual runs, but allow Docker to override it with "redis"
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Stream Name (Must match what router.py expects)
    REDIS_STREAM_NAME: str = "zombie_traffic"
    
    # Rate Limiting
    RATE_LIMIT_COUNT: int = 5
    RATE_LIMIT_WINDOW: int = 60

    class Config:
        env_file = ".env"

settings = Settings()