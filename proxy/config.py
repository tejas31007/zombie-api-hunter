from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CHANGED: Now pointing to our local Java app
    TARGET_URL: str = "http://127.0.0.1:8080"

    class Config:
        env_file = ".env"

settings = Settings()