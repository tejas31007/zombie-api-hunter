from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Target (The Java Victim)
    TARGET_URL: str = "http://127.0.0.1:8080"
    
    # Redis (The Brain & Memory)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "traffic_logs"
    
    # Rate Limiting (The Speed Limit)
    RATE_LIMIT_COUNT: int = 5       # Max requests
    RATE_LIMIT_WINDOW: int = 60     # Per X seconds

    class Config:
        env_file = ".env"

settings = Settings()