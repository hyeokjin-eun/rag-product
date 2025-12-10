# 도메인 개발 에이전트

비즈니스 로직 구현 가이드

## 작업 흐름

```
1. 도메인 요구사항 분석
   ↓
2. 스키마 정의 (schemas.py)
   ↓
3. 레포지토리 구현 (repository.py) - 필요시
   ↓
4. 서비스 구현 (service.py)
   ↓
5. 테스트 작성
```

## 파일 위치

| 구분 | 경로 |
|------|------|
| 서비스 | `app/domains/{domain}/service.py` |
| 스키마 | `app/domains/{domain}/schemas.py` |
| 레포지토리 | `app/domains/{domain}/repository.py` |

## 도메인 목록

| 도메인 | 역할 |
|--------|------|
| documents | 문서 업로드, 파싱, 청킹 |
| embeddings | 벡터 임베딩 생성 |
| search | 벡터 유사도 검색 |
| rag | RAG 파이프라인 오케스트레이션 |

## 구현 패턴

### 1. 스키마 정의

```python
# app/domains/documents/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str
    metadata: dict | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    status: DocumentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentSchema(BaseModel):
    """내부 사용 스키마"""
    id: str
    title: str
    content: str
    chunks: list[str] = []
    metadata: dict = {}
```

### 2. 서비스 구현

```python
# app/domains/documents/service.py
from app.domains.documents.schemas import (
    DocumentUploadRequest,
    DocumentResponse,
    DocumentSchema,
)
from app.infrastructure.qdrant.client import QdrantClient


class DocumentService:
    def __init__(self, qdrant: QdrantClient):
        self.qdrant = qdrant

    async def upload(self, request: DocumentUploadRequest) -> DocumentResponse:
        """문서 업로드 및 처리"""
        # 1. 문서 생성
        document = DocumentSchema(
            id=self._generate_id(),
            title=request.title,
            content=request.content,
            metadata=request.metadata or {},
        )

        # 2. 청킹
        document.chunks = self._chunk_text(document.content)

        # 3. 저장
        await self.qdrant.upsert(document)

        return DocumentResponse(
            id=document.id,
            title=document.title,
            status="pending",
            created_at=datetime.utcnow(),
        )

    async def get(self, document_id: str) -> DocumentResponse | None:
        """문서 조회"""
        document = await self.qdrant.get(document_id)
        if not document:
            return None
        return DocumentResponse.model_validate(document)

    def _generate_id(self) -> str:
        import uuid
        return str(uuid.uuid4())

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        """텍스트 청킹"""
        # 간단한 청킹 로직
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
```

### 3. 레포지토리 (선택)

```python
# app/domains/documents/repository.py
from app.domains.documents.schemas import DocumentSchema
from app.infrastructure.qdrant.client import QdrantClient


class DocumentRepository:
    def __init__(self, qdrant: QdrantClient):
        self.qdrant = qdrant
        self.collection = "documents"

    async def save(self, document: DocumentSchema) -> None:
        await self.qdrant.upsert(self.collection, document)

    async def find_by_id(self, document_id: str) -> DocumentSchema | None:
        return await self.qdrant.get(self.collection, document_id)

    async def delete(self, document_id: str) -> bool:
        return await self.qdrant.delete(self.collection, document_id)
```

## 체크리스트

- [ ] 스키마에 Field 검증 추가
- [ ] 서비스 메서드는 async로 구현
- [ ] 외부 의존성은 생성자 주입
- [ ] 에러 상황 처리
- [ ] 타입 힌트 명시

## 도메인 간 의존성 규칙

```
rag → search → embeddings → (providers)
         ↘      ↓
          documents
              ↓
         infrastructure
```

- 상위 도메인이 하위 도메인을 참조
- 동일 레벨 도메인 간 직접 참조 금지
- infrastructure는 모든 도메인에서 사용 가능