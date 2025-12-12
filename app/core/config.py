"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 26333

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 26379

    # Temporal
    temporal_host: str = "localhost"
    temporal_port: int = 27233

    model_config = {"env_file": ".env"}


settings = Settings()
