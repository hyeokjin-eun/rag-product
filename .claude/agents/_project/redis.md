# Redis 에이전트

캐싱 및 세션 관리 가이드

## 파일 위치

| 구분 | 경로 |
|------|------|
| 클라이언트 | `app/infrastructure/redis/client.py` |
| 설정 | `app/core/config.py` |

## 접속 정보

| 서비스 | URL |
|--------|-----|
| Redis | localhost:26379 |

## 용도

| 용도 | 설명 |
|------|------|
| 캐싱 | 임베딩 결과, 검색 결과 캐시 |
| Rate Limiting | API 호출 제한 |
| 세션 | 사용자 세션 관리 (필요시) |
| 큐 | 간단한 작업 큐 (Temporal 대안) |

## 구현 패턴

### 1. 클라이언트 구현

```python
# app/infrastructure/redis/client.py
import json
from typing import Any
from redis.asyncio import Redis
from app.core.config import settings


class RedisClient:
    """Redis 클라이언트"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        db: int = 0,
    ):
        self.redis = Redis(
            host=host or settings.redis_host,
            port=port or settings.redis_port,
            db=db,
            decode_responses=True,
        )

    async def get(self, key: str) -> Any | None:
        """값 조회"""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None,
    ) -> bool:
        """값 저장"""
        serialized = json.dumps(value)
        if ttl:
            await self.redis.setex(key, ttl, serialized)
        else:
            await self.redis.set(key, serialized)
        return True

    async def delete(self, key: str) -> bool:
        """값 삭제"""
        await self.redis.delete(key)
        return True

    async def exists(self, key: str) -> bool:
        """키 존재 여부"""
        return await self.redis.exists(key) > 0

    async def expire(self, key: str, ttl: int) -> bool:
        """TTL 설정"""
        await self.redis.expire(key, ttl)
        return True

    async def incr(self, key: str) -> int:
        """카운터 증가"""
        return await self.redis.incr(key)

    async def keys(self, pattern: str) -> list[str]:
        """패턴으로 키 조회"""
        return await self.redis.keys(pattern)

    async def flush_pattern(self, pattern: str) -> int:
        """패턴 매칭 키 삭제"""
        keys = await self.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0

    async def close(self):
        """연결 종료"""
        await self.redis.close()
```

### 2. 캐시 데코레이터

```python
# app/infrastructure/redis/cache.py
import hashlib
import json
from functools import wraps
from typing import Callable
from app.infrastructure.redis.client import RedisClient


def cached(
    prefix: str,
    ttl: int = 3600,
    key_builder: Callable = None,
):
    """캐시 데코레이터"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_data = json.dumps({"args": args[1:], "kwargs": kwargs}, sort_keys=True)
                hash_key = hashlib.md5(key_data.encode()).hexdigest()
                cache_key = f"{prefix}:{hash_key}"

            # 캐시 조회
            client = RedisClient()
            cached_value = await client.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 함수 실행 및 캐시 저장
            result = await func(*args, **kwargs)
            await client.set(cache_key, result, ttl=ttl)

            return result
        return wrapper
    return decorator


# 사용 예시
class EmbeddingService:
    @cached(prefix="embedding", ttl=86400)  # 24시간
    async def embed(self, text: str) -> list[float]:
        # 실제 임베딩 생성 (비용 발생)
        return await self.provider.embed_single(text)
```

### 3. Rate Limiter

```python
# app/infrastructure/redis/rate_limiter.py
from app.infrastructure.redis.client import RedisClient


class RateLimiter:
    """Rate Limiter"""

    def __init__(self, client: RedisClient):
        self.client = client

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window: int = 60,
    ) -> tuple[bool, int]:
        """
        요청 허용 여부 확인

        Args:
            key: 제한 키 (예: user_id, ip)
            limit: 윈도우당 최대 요청 수
            window: 윈도우 크기 (초)

        Returns:
            (허용 여부, 남은 요청 수)
        """
        rate_key = f"rate:{key}"

        current = await self.client.incr(rate_key)
        if current == 1:
            await self.client.expire(rate_key, window)

        remaining = max(0, limit - current)
        allowed = current <= limit

        return allowed, remaining


# FastAPI 의존성으로 사용
from fastapi import HTTPException, Request

async def rate_limit_dependency(request: Request):
    client = RedisClient()
    limiter = RateLimiter(client)

    key = request.client.host
    allowed, remaining = await limiter.is_allowed(key, limit=100, window=60)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"X-RateLimit-Remaining": str(remaining)},
        )
```

### 4. 설정

```python
# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Cache TTL
    embedding_cache_ttl: int = 86400  # 24시간
    search_cache_ttl: int = 3600      # 1시간

    model_config = {"env_file": ".env"}


settings = Settings()
```

### 5. 의존성 주입

```python
# app/core/dependencies.py
from app.infrastructure.redis.client import RedisClient


def get_redis_client() -> RedisClient:
    return RedisClient()
```

## 캐시 키 설계

| 용도 | 키 패턴 | TTL |
|------|---------|-----|
| 임베딩 캐시 | `embedding:{hash}` | 24시간 |
| 검색 결과 | `search:{query_hash}` | 1시간 |
| Rate Limit | `rate:{ip}` | 1분 |
| 세션 | `session:{token}` | 24시간 |

## 체크리스트

- [ ] RedisClient 클래스 구현
- [ ] 설정에 host/port 추가
- [ ] 캐시 데코레이터 구현
- [ ] Rate Limiter 구현 (필요시)
- [ ] 의존성 주입 설정
- [ ] 연결 테스트

## 주의사항

- `decode_responses=True`로 문자열 자동 디코딩
- JSON 직렬화 가능한 데이터만 캐시 가능
- 대용량 데이터는 압축 고려 (gzip)
- 프로덕션에서는 Redis Cluster 또는 Sentinel 고려
