# API 개발 에이전트

FastAPI 엔드포인트 구현 가이드

## 작업 흐름

```
1. 요구사항 분석
   ↓
2. 스키마 정의 (schemas.py)
   ↓
3. 라우터 구현 (api/v1/*.py)
   ↓
4. 서비스 연동 (domains/*/service.py)
   ↓
5. 테스트 작성
```

## 파일 위치

| 구분 | 경로 |
|------|------|
| 라우터 | `app/api/v1/{resource}.py` |
| 라우터 통합 | `app/api/router.py` |
| 의존성 | `app/core/dependencies.py` |

## 구현 패턴

### 1. 라우터 파일 생성

```python
# app/api/v1/documents.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.domains.documents.schemas import (
    DocumentUploadRequest,
    DocumentResponse,
)
from app.domains.documents.service import DocumentService
from app.core.dependencies import get_document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: DocumentUploadRequest,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """문서 업로드"""
    return await service.upload(request)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """문서 조회"""
    document = await service.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
```

### 2. 라우터 등록

```python
# app/api/router.py
from fastapi import APIRouter
from app.api.v1 import documents, search, collections

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(collections.router)
```

### 3. 의존성 주입

```python
# app/core/dependencies.py
from functools import lru_cache
from app.domains.documents.service import DocumentService
from app.infrastructure.qdrant.client import QdrantClient


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient()


def get_document_service() -> DocumentService:
    return DocumentService(qdrant=get_qdrant_client())
```

## 체크리스트

- [ ] 라우터에 prefix와 tags 설정
- [ ] response_model로 응답 타입 명시
- [ ] status_code 적절히 설정
- [ ] Depends로 서비스 주입
- [ ] HTTPException으로 에러 처리
- [ ] Docstring 작성

## 주의사항

- 라우터에 비즈니스 로직 작성 금지 → 서비스로 위임
- 직접 DB 접근 금지 → 서비스/레포지토리 통해 접근
- 요청/응답 스키마 반드시 정의
