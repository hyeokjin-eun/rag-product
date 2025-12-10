# Schema Builder 에이전트

스펙 문서를 기반으로 Pydantic 스키마를 생성합니다.

## 역할

- 엔티티 스키마 생성
- Request/Response 모델 생성
- 검증 규칙 적용
- Enum 타입 정의

## 입력

- 스펙 문서 2장 "데이터 모델"
- 스펙 문서 3장 "API 명세" (Request/Response)
- 스펙 문서 4.2장 "검증 규칙"

## 출력

`app/domains/{domain}/schemas.py` 파일

## 구현 프로세스

### 1. 스펙 분석

```
스펙 2장에서 추출:
├── 엔티티 필드 목록
├── 필드 타입
├── 필수/선택 여부
├── 제약조건
└── 상태값 (Enum)

스펙 3장에서 추출:
├── Request 필드
├── Response 필드
└── 필드별 설명
```

### 2. 타입 매핑

| 스펙 타입 | Python 타입 | Pydantic |
|-----------|-------------|----------|
| string | str | str |
| integer | int | int |
| number | float | float |
| boolean | bool | bool |
| datetime | datetime | datetime |
| uuid | str | str (UUID v4 패턴) |
| array | list | list[T] |
| object | dict | dict 또는 중첩 모델 |
| enum | Enum | StrEnum |

### 3. 스키마 구조

```python
# app/domains/{domain}/schemas.py

from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict


# ===== Enums =====

class {Domain}Status(StrEnum):
    """상태값 정의"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ===== Base Schemas =====

class {Domain}Base(BaseModel):
    """공통 필드"""
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="제목"
    )


# ===== Request Schemas =====

class {Domain}CreateRequest({Domain}Base):
    """생성 요청"""
    content: str = Field(..., description="내용")
    metadata: dict | None = Field(default=None, description="메타데이터")


class {Domain}UpdateRequest(BaseModel):
    """수정 요청 (모든 필드 선택)"""
    title: str | None = Field(default=None, max_length=200)
    metadata: dict | None = None


# ===== Response Schemas =====

class {Domain}Response({Domain}Base):
    """단일 응답"""
    id: str
    status: {Domain}Status
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class {Domain}ListResponse(BaseModel):
    """목록 응답"""
    items: list[{Domain}Response]
    total: int
    page: int
    limit: int


# ===== Internal Schemas =====

class {Domain}Schema(BaseModel):
    """내부 사용 스키마 (DB 모델 대응)"""
    id: str
    title: str
    content: str
    status: {Domain}Status = {Domain}Status.PENDING
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None
```

### 4. 검증 규칙 적용

스펙 4.2장의 검증 규칙을 Field()에 적용:

```python
# 문자열 제약
title: str = Field(
    ...,
    min_length=1,
    max_length=200,
    pattern=r'^[\w\s\-\.]+$',  # 정규식 패턴
    description="제목 (1-200자, 영숫자/공백/-/.만 허용)"
)

# 숫자 제약
score: float = Field(
    ...,
    ge=0.0,      # 이상
    le=1.0,      # 이하
    description="점수 (0.0-1.0)"
)

# 리스트 제약
tags: list[str] = Field(
    default_factory=list,
    max_length=10,  # 최대 10개
    description="태그 목록"
)

# 커스텀 검증
from pydantic import field_validator

class CreateRequest(BaseModel):
    filename: str

    @field_validator('filename')
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if '/' in v or '\\' in v:
            raise ValueError('파일명에 경로 문자를 포함할 수 없습니다')
        return v
```

### 5. 특수 타입 처리

```python
from pydantic import EmailStr, HttpUrl
from typing import Annotated
from uuid import UUID

# 이메일
email: EmailStr

# URL
url: HttpUrl

# UUID (문자열로 저장하되 형식 검증)
id: Annotated[str, Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')]

# 또는 UUID 타입 직접 사용
from uuid import UUID
id: UUID
```

### 6. 중첩 모델

```python
# 메타데이터 구조화
class DocumentMetadata(BaseModel):
    source: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)


class DocumentCreateRequest(BaseModel):
    title: str
    content: str
    metadata: DocumentMetadata | None = None
```

### 7. 응답 예시 추가 (OpenAPI)

```python
class DocumentResponse(BaseModel):
    id: str
    title: str
    status: DocumentStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "샘플 문서",
                "status": "completed",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }
    )
```

## 출력 파일 구조

```python
# app/domains/{domain}/schemas.py

"""
{Domain} 도메인 스키마 정의

스펙 문서: .claude/specs/{domain}.md
"""

from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, field_validator

# ===== Enums =====
# 스펙 2장 상태값 기반

# ===== Request Schemas =====
# 스펙 3장 Request 기반

# ===== Response Schemas =====
# 스펙 3장 Response 기반

# ===== Internal Schemas =====
# 스펙 2장 엔티티 기반
```

## 체크리스트

- [ ] 스펙 2장의 모든 엔티티 필드 반영됨
- [ ] 스펙 3장의 Request/Response 모델 생성됨
- [ ] 스펙 4.2장 검증 규칙 Field()에 적용됨
- [ ] 상태값은 StrEnum으로 정의됨
- [ ] 필수/선택 필드 구분됨 (... vs None)
- [ ] from_attributes=True 설정됨 (ORM 호환)
- [ ] description 추가됨 (API 문서용)
