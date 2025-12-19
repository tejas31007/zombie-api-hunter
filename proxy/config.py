import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Target (The Java Victim)
    # If running in Docker, we use 'host.docker.internal' to reach your laptop
    TARGET_URL: str = os.getenv("TARGET_URL", "http://host.docker.internal:8080")

    # Redis (The Brain & Memory)
    # We check for an Env Var 'REDIS_HOST'. If not found, default to 'localhost'
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "traffic_logs"

    # Rate Limiting (The Speed Limit)
    RATE_LIMIT_COUNT: int = 5  # Max requests
    RATE_LIMIT_WINDOW: int = 60  # Per X seconds

    class Config:
        env_file = ".env"


settings = Settings()
