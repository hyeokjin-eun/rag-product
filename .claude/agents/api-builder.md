# API Builder 에이전트

스펙 문서를 기반으로 FastAPI 라우터를 구현합니다.

## 역할

- API 엔드포인트 구현
- 요청/응답 처리
- 에러 응답 매핑
- OpenAPI 문서화

## 입력

- 스펙 문서 3장 "API 명세"
- 스펙 문서 6장 "에러 처리"
- `schemas.py` (Schema Builder 결과물)
- `service.py` (Service Builder 결과물)

## 출력

- `app/api/v1/{domain}.py` 파일
- `app/api/router.py` 수정

## 구현 프로세스

### 1. 스펙 분석

```
스펙 3장에서 추출:
├── 엔드포인트 목록 (Method, Path)
├── 각 엔드포인트 상세:
│   ├── Request 형식
│   ├── Response 형식
│   ├── 상태 코드
│   └── 에러 응답
└── 인증 요구사항

스펙 6장에서 추출:
├── 에러 코드 → HTTP 상태 코드 매핑
└── 에러 응답 형식
```

### 2. 라우터 구조

```python
# app/api/v1/{domain}.py

"""
{Domain} API 라우터

스펙 문서: .claude/specs/{domain}.md
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from app.domains.{domain}.schemas import (
    {Domain}CreateRequest,
    {Domain}UpdateRequest,
    {Domain}Response,
    {Domain}ListResponse,
)
from app.domains.{domain}.service import {Domain}Service
from app.core.dependencies import get_{domain}_service
from app.core.exceptions import {Domain}NotFoundError, {Domain}ValidationError

router = APIRouter(
    prefix="/{domain}s",
    tags=["{Domain}s"],
)


# ===== Error Handlers =====

@router.exception_handler({Domain}NotFoundError)
async def not_found_handler(request, exc: {Domain}NotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"code": exc.code, "message": exc.message},
    )


# ===== Endpoints =====

@router.post(
    "/",
    response_model={Domain}Response,
    status_code=status.HTTP_201_CREATED,
    summary="생성",
    description="새로운 {domain}을 생성합니다.",
)
async def create_{domain}(
    request: {Domain}CreateRequest,
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}Response:
    """
    ## 생성

    새로운 {domain}을 생성합니다.

    - **title**: 제목 (필수, 1-200자)
    - **content**: 내용 (필수)
    - **metadata**: 메타데이터 (선택)
    """
    return await service.create(request)


@router.get(
    "/{id}",
    response_model={Domain}Response,
    summary="단일 조회",
)
async def get_{domain}(
    id: str,
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}Response:
    """ID로 {domain}을 조회합니다."""
    return await service.get(id)


@router.get(
    "/",
    response_model={Domain}ListResponse,
    summary="목록 조회",
)
async def list_{domain}s(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 개수"),
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}ListResponse:
    """
    {domain} 목록을 조회합니다.

    페이지네이션을 지원합니다.
    """
    return await service.list(page=page, limit=limit)


@router.patch(
    "/{id}",
    response_model={Domain}Response,
    summary="수정",
)
async def update_{domain}(
    id: str,
    request: {Domain}UpdateRequest,
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}Response:
    """
    {domain}을 수정합니다.

    변경할 필드만 전송하면 됩니다.
    """
    return await service.update(id, request)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="삭제",
)
async def delete_{domain}(
    id: str,
    service: {Domain}Service = Depends(get_{domain}_service),
) -> None:
    """
    {domain}을 삭제합니다.

    삭제된 {domain}은 복구할 수 없습니다.
    """
    await service.delete(id)
```

### 3. 에러 응답 처리

스펙 6장의 에러 매핑:

```python
# app/core/exception_handlers.py

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    {Domain}NotFoundError,
    {Domain}ValidationError,
    {Domain}StateError,
)

# 에러 코드 → HTTP 상태 코드 매핑
ERROR_STATUS_MAP = {
    "{DOMAIN}_NOT_FOUND": 404,
    "{DOMAIN}_VALIDATION_ERROR": 400,
    "{DOMAIN}_INVALID_STATE": 409,
    "{DOMAIN}_UNAUTHORIZED": 401,
    "{DOMAIN}_FORBIDDEN": 403,
}


async def domain_exception_handler(request: Request, exc: {Domain}Error):
    status_code = ERROR_STATUS_MAP.get(exc.code, 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )


# main.py에서 등록
# app.add_exception_handler({Domain}Error, domain_exception_handler)
```

### 4. 인증 적용

스펙 3장의 인증 요구사항 적용:

```python
from app.core.dependencies import get_current_user
from app.core.auth import User

@router.post("/")
async def create_{domain}(
    request: {Domain}CreateRequest,
    current_user: User = Depends(get_current_user),  # 인증 필수
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}Response:
    return await service.create(request, user_id=current_user.id)


# 권한 검증이 필요한 경우
from app.core.dependencies import require_role

@router.delete("/{id}")
async def delete_{domain}(
    id: str,
    current_user: User = Depends(require_role("admin")),  # admin만
    service: {Domain}Service = Depends(get_{domain}_service),
) -> None:
    await service.delete(id)
```

### 5. 필터/정렬 지원

```python
from enum import StrEnum
from typing import Annotated

class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"

class {Domain}SortField(StrEnum):
    CREATED_AT = "created_at"
    TITLE = "title"


@router.get("/")
async def list_{domain}s(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: {Domain}Status | None = Query(default=None, description="상태 필터"),
    sort_by: {Domain}SortField = Query(default={Domain}SortField.CREATED_AT),
    order: SortOrder = Query(default=SortOrder.DESC),
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}ListResponse:
    return await service.list(
        page=page,
        limit=limit,
        status=status,
        sort_by=sort_by,
        order=order,
    )
```

### 6. 파일 업로드

```python
from fastapi import UploadFile, File

@router.post("/upload")
async def upload_{domain}(
    file: UploadFile = File(..., description="업로드할 파일"),
    title: str = Query(..., max_length=200),
    service: {Domain}Service = Depends(get_{domain}_service),
) -> {Domain}Response:
    """
    파일을 업로드하여 {domain}을 생성합니다.

    허용 형식: PDF, TXT, MD
    최대 크기: 10MB
    """
    # 파일 검증
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기가 10MB를 초과합니다")

    content = await file.read()
    return await service.create_from_file(
        title=title,
        filename=file.filename,
        content=content,
    )
```

### 7. 라우터 등록

```python
# app/api/router.py

from fastapi import APIRouter
from app.api.v1 import documents, search, collections

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(documents.router)
api_router.include_router(search.router)
api_router.include_router(collections.router)


# app/main.py

from fastapi import FastAPI
from app.api.router import api_router

app = FastAPI(
    title="RAG API",
    version="1.0.0",
)

app.include_router(api_router)
```

### 8. OpenAPI 응답 문서화

```python
from fastapi import APIRouter

router = APIRouter(
    prefix="/{domain}s",
    tags=["{Domain}s"],
    responses={
        401: {"description": "인증 실패"},
        403: {"description": "권한 없음"},
        500: {"description": "서버 오류"},
    },
)


@router.get(
    "/{id}",
    response_model={Domain}Response,
    responses={
        200: {
            "description": "조회 성공",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "샘플",
                        "status": "completed",
                    }
                }
            },
        },
        404: {
            "description": "문서 없음",
            "content": {
                "application/json": {
                    "example": {"code": "DOCUMENT_NOT_FOUND", "message": "문서를 찾을 수 없습니다"}
                }
            },
        },
    },
)
async def get_{domain}(id: str) -> {Domain}Response:
    ...
```

## 출력 파일 구조

```python
# app/api/v1/{domain}.py

"""
{Domain} API
스펙 문서: .claude/specs/{domain}.md
"""

# Imports

router = APIRouter(prefix="/{domain}s", tags=["{Domain}s"])

# ===== Endpoints =====
# POST   /           - 생성
# GET    /{id}       - 단일 조회
# GET    /           - 목록 조회
# PATCH  /{id}       - 수정
# DELETE /{id}       - 삭제
# (추가 엔드포인트...)
```

## 체크리스트

- [ ] 스펙 3장의 모든 엔드포인트 구현됨
- [ ] 각 엔드포인트에 적절한 HTTP 메서드/상태코드 사용
- [ ] Request/Response 스키마 적용됨
- [ ] 스펙 6장 에러 응답 매핑됨
- [ ] 인증 요구사항 적용됨 (해당시)
- [ ] 페이지네이션 구현됨 (해당시)
- [ ] 필터/정렬 구현됨 (해당시)
- [ ] router.py에 등록됨
- [ ] OpenAPI 문서화 (summary, description)
