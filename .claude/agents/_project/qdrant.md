# Qdrant 에이전트

벡터 데이터베이스 연동 가이드

## 파일 위치

| 구분 | 경로 |
|------|------|
| 클라이언트 | `app/infrastructure/qdrant/client.py` |
| 설정 | `app/core/config.py` |

## 접속 정보

| 서비스 | URL |
|--------|-----|
| REST API | http://localhost:26333 |
| gRPC API | localhost:26334 |
| Dashboard | http://localhost:26333/dashboard |

## 구현 패턴

### 1. 클라이언트 구현

```python
# app/infrastructure/qdrant/client.py
from qdrant_client import QdrantClient as BaseQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from app.core.config import settings


class QdrantClient:
    """Qdrant 벡터 데이터베이스 클라이언트"""

    def __init__(
        self,
        host: str = None,
        port: int = None,
    ):
        self.client = BaseQdrantClient(
            host=host or settings.qdrant_host,
            port=port or settings.qdrant_port,
        )

    async def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
    ) -> bool:
        """컬렉션 생성"""
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=distance,
            ),
        )
        return True

    async def collection_exists(self, collection_name: str) -> bool:
        """컬렉션 존재 여부 확인"""
        collections = self.client.get_collections()
        return any(c.name == collection_name for c in collections.collections)

    async def upsert(
        self,
        collection_name: str,
        ids: list[str],
        vectors: list[list[float]],
        payloads: list[dict] = None,
    ) -> bool:
        """벡터 삽입/업데이트"""
        points = [
            PointStruct(
                id=id,
                vector=vector,
                payload=payload or {},
            )
            for id, vector, payload in zip(
                ids,
                vectors,
                payloads or [{}] * len(ids),
            )
        ]
        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )
        return True

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float = None,
        filter_conditions: dict = None,
    ) -> list[dict]:
        """유사도 검색"""
        query_filter = None
        if filter_conditions:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value),
                    )
                    for key, value in filter_conditions.items()
                ]
            )

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=query_filter,
        )

        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
            }
            for result in results
        ]

    async def get(
        self,
        collection_name: str,
        ids: list[str],
    ) -> list[dict]:
        """ID로 조회"""
        results = self.client.retrieve(
            collection_name=collection_name,
            ids=ids,
        )
        return [
            {
                "id": result.id,
                "payload": result.payload,
            }
            for result in results
        ]

    async def delete(
        self,
        collection_name: str,
        ids: list[str],
    ) -> bool:
        """벡터 삭제"""
        self.client.delete(
            collection_name=collection_name,
            points_selector=ids,
        )
        return True

    async def delete_collection(self, collection_name: str) -> bool:
        """컬렉션 삭제"""
        self.client.delete_collection(collection_name=collection_name)
        return True
```

### 2. 설정

```python
# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    model_config = {"env_file": ".env"}


settings = Settings()
```

### 3. 의존성 주입

```python
# app/core/dependencies.py
from functools import lru_cache
from app.infrastructure.qdrant.client import QdrantClient


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient()
```

### 4. 사용 예시

```python
# 컬렉션 생성
await client.create_collection(
    collection_name="documents",
    vector_size=1536,  # OpenAI embedding dimension
)

# 벡터 저장
await client.upsert(
    collection_name="documents",
    ids=["doc-001", "doc-002"],
    vectors=[[0.1, 0.2, ...], [0.3, 0.4, ...]],
    payloads=[
        {"title": "문서1", "content": "내용1"},
        {"title": "문서2", "content": "내용2"},
    ],
)

# 유사도 검색
results = await client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    limit=5,
    score_threshold=0.7,
)

# 필터링 검색
results = await client.search(
    collection_name="documents",
    query_vector=[0.1, 0.2, ...],
    filter_conditions={"category": "tech"},
)
```

## 컬렉션 설계

### RAG 프로젝트 컬렉션

| 컬렉션 | 용도 | 벡터 차원 |
|--------|------|----------|
| documents | 문서 청크 벡터 | 1536 (OpenAI) |
| queries | 쿼리 캐시 (선택) | 1536 |

### 페이로드 스키마

```python
# documents 컬렉션
{
    "document_id": "uuid",      # 원본 문서 ID
    "chunk_index": 0,           # 청크 순서
    "content": "텍스트 내용",    # 원본 텍스트
    "metadata": {               # 메타데이터
        "title": "문서 제목",
        "source": "파일명",
        "created_at": "2024-01-01T00:00:00Z",
    },
}
```

## 체크리스트

- [ ] QdrantClient 클래스 구현
- [ ] 설정에 host/port 추가
- [ ] 컬렉션 생성 로직 구현
- [ ] upsert/search/delete 메서드 구현
- [ ] 의존성 주입 설정
- [ ] 연결 테스트

## 주의사항

- 컬렉션 생성 시 vector_size는 임베딩 모델과 일치해야 함
- 대량 upsert 시 배치 처리 권장 (1000개 단위)
- 프로덕션에서는 gRPC 포트(6334) 사용 권장
