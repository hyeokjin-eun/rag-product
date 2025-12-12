"""FastAPI dependency injection."""

from functools import lru_cache

from app.core.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# TODO: Add infrastructure dependencies
# from app.infrastructure.qdrant.client import QdrantClient
# from app.infrastructure.redis.client import RedisClient
#
# @lru_cache
# def get_qdrant_client() -> QdrantClient:
#     return QdrantClient()
#
# @lru_cache
# def get_redis_client() -> RedisClient:
#     return RedisClient()
