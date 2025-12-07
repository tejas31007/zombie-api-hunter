from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Target (The Java Victim)
    TARGET_URL: str = "http://127.0.0.1:8080"

    # Database (The Brain)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_QUEUE_NAME: str = "traffic_log"  # The name of our list

    class Config:
        env_file = ".env"

settings = Settings()