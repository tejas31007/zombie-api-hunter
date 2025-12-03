from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # The URL where the "Victim" app lives
    # For now, we use a public test API. Later, we change this to http://localhost:8080
    TARGET_URL: str = "https://jsonplaceholder.typicode.com"

    class Config:
        env_file = ".env"

settings = Settings()