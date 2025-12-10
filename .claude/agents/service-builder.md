# Service Builder 에이전트

스펙 문서를 기반으로 서비스 클래스를 구현합니다.

## 역할

- 비즈니스 로직 구현
- 트랜잭션 처리
- 에러 핸들링
- 외부 서비스 연동

## 입력

- 스펙 문서 4장 "비즈니스 로직"
- 스펙 문서 5장 "외부 연동"
- 스펙 문서 6장 "에러 처리"
- `schemas.py` (Schema Builder 결과물)

## 출력

`app/domains/{domain}/service.py` 파일

## 구현 프로세스

### 1. 스펙 분석

```
스펙 4장에서 추출:
├── 핵심 비즈니스 규칙
├── 검증 로직
├── 프로세스 흐름
└── 상태 전이

스펙 5장에서 추출:
├── 의존하는 도메인
├── 외부 서비스 목록
└── 연동 방식

스펙 6장에서 추출:
├── 에러 코드
├── 에러 조건
└── 재시도 정책
```

### 2. 서비스 구조

```python
# app/domains/{domain}/service.py

"""
{Domain} 서비스

비즈니스 로직을 처리합니다.
스펙 문서: .claude/specs/{domain}.md
"""

from datetime import datetime
from uuid import uuid4

from app.domains.{domain}.schemas import (
    {Domain}CreateRequest,
    {Domain}UpdateRequest,
    {Domain}Response,
    {Domain}ListResponse,
    {Domain}Schema,
    {Domain}Status,
)
from app.domains.{domain}.repository import {Domain}Repository
from app.core.exceptions import {Domain}NotFoundError, {Domain}ValidationError


class {Domain}Service:
    """
    {Domain} 서비스

    책임:
    - {스펙 1.2장 책임 범위 참조}
    """

    def __init__(
        self,
        repository: {Domain}Repository,
        # 다른 의존성...
    ):
        self.repository = repository

    async def create(self, request: {Domain}CreateRequest) -> {Domain}Response:
        """
        생성

        비즈니스 규칙:
        - {스펙 4.1장 규칙 참조}
        """
        # 1. 검증
        self._validate_create(request)

        # 2. 엔티티 생성
        entity = {Domain}Schema(
            id=str(uuid4()),
            title=request.title,
            content=request.content,
            status={Domain}Status.PENDING,
            metadata=request.metadata or {},
            created_at=datetime.utcnow(),
        )

        # 3. 저장
        await self.repository.save(entity)

        # 4. 응답 변환
        return {Domain}Response.model_validate(entity)

    async def get(self, id: str) -> {Domain}Response:
        """단일 조회"""
        entity = await self.repository.find_by_id(id)
        if not entity:
            raise {Domain}NotFoundError(id)
        return {Domain}Response.model_validate(entity)

    async def list(
        self,
        page: int = 1,
        limit: int = 20,
        **filters,
    ) -> {Domain}ListResponse:
        """목록 조회"""
        items, total = await self.repository.find_all(
            page=page,
            limit=limit,
            **filters,
        )
        return {Domain}ListResponse(
            items=[{Domain}Response.model_validate(item) for item in items],
            total=total,
            page=page,
            limit=limit,
        )

    async def update(
        self,
        id: str,
        request: {Domain}UpdateRequest,
    ) -> {Domain}Response:
        """수정"""
        entity = await self.repository.find_by_id(id)
        if not entity:
            raise {Domain}NotFoundError(id)

        # 변경된 필드만 업데이트
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(entity, key, value)
        entity.updated_at = datetime.utcnow()

        await self.repository.save(entity)
        return {Domain}Response.model_validate(entity)

    async def delete(self, id: str) -> bool:
        """삭제"""
        entity = await self.repository.find_by_id(id)
        if not entity:
            raise {Domain}NotFoundError(id)

        return await self.repository.delete(id)

    # ===== Private Methods =====

    def _validate_create(self, request: {Domain}CreateRequest) -> None:
        """
        생성 검증

        스펙 4.2장 검증 규칙 참조
        """
        # 예: 중복 검증
        # if await self.repository.exists_by_title(request.title):
        #     raise {Domain}ValidationError("이미 존재하는 제목입니다")
        pass

    def _can_transition(
        self,
        current: {Domain}Status,
        target: {Domain}Status,
    ) -> bool:
        """
        상태 전이 검증

        스펙 2장 상태 다이어그램 참조
        """
        allowed_transitions = {
            {Domain}Status.PENDING: [{Domain}Status.PROCESSING, {Domain}Status.FAILED],
            {Domain}Status.PROCESSING: [{Domain}Status.COMPLETED, {Domain}Status.FAILED],
            {Domain}Status.FAILED: [{Domain}Status.PENDING],  # 재시도
        }
        return target in allowed_transitions.get(current, [])
```

### 3. 비즈니스 규칙 구현

스펙 4.1장의 각 규칙을 메서드로 구현:

```python
# 규칙 예시: "문서 내용은 1000자 이상이어야 청킹이 실행된다"
def _should_chunk(self, content: str) -> bool:
    """청킹 필요 여부 판단"""
    return len(content) >= 1000

# 규칙 예시: "처리 중인 문서는 삭제할 수 없다"
def _can_delete(self, entity: {Domain}Schema) -> bool:
    """삭제 가능 여부 판단"""
    return entity.status != {Domain}Status.PROCESSING
```

### 4. 에러 핸들링

스펙 6장의 에러 코드에 맞는 예외 발생:

```python
# app/core/exceptions.py

class {Domain}Error(Exception):
    """기본 예외"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


class {Domain}NotFoundError({Domain}Error):
    """조회 실패"""
    def __init__(self, id: str):
        super().__init__(
            message=f"문서를 찾을 수 없습니다: {id}",
            code="{DOMAIN}_NOT_FOUND",
        )


class {Domain}ValidationError({Domain}Error):
    """검증 실패"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            code="{DOMAIN}_VALIDATION_ERROR",
        )


class {Domain}StateError({Domain}Error):
    """상태 전이 실패"""
    def __init__(self, current: str, target: str):
        super().__init__(
            message=f"상태를 {current}에서 {target}로 변경할 수 없습니다",
            code="{DOMAIN}_INVALID_STATE",
        )
```

### 5. 외부 서비스 연동

스펙 5장의 연동 요구사항 구현:

```python
class {Domain}Service:
    def __init__(
        self,
        repository: {Domain}Repository,
        embedding_service: EmbeddingService,  # 다른 도메인
        qdrant_client: QdrantClient,          # 인프라
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.qdrant = qdrant_client

    async def process(self, id: str) -> None:
        """
        처리 (외부 서비스 연동)

        1. 임베딩 생성 (embedding_service)
        2. 벡터 저장 (qdrant)
        """
        entity = await self.get(id)

        # 임베딩 생성
        embeddings = await self.embedding_service.embed(
            [entity.content]
        )

        # Qdrant에 저장
        await self.qdrant.upsert(
            collection="documents",
            points=[{
                "id": entity.id,
                "vector": embeddings[0],
                "payload": {"title": entity.title},
            }]
        )
```

### 6. 재시도/타임아웃 처리

스펙 6.2장 재시도 정책 적용:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class {Domain}Service:

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=30),
        reraise=True,
    )
    async def _call_external_api(self, data: dict) -> dict:
        """외부 API 호출 (재시도 적용)"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(URL, json=data)
            response.raise_for_status()
            return response.json()
```

## 출력 파일 구조

```python
# app/domains/{domain}/service.py

"""
{Domain} 서비스
스펙 문서: .claude/specs/{domain}.md
"""

# Imports

# ===== Service Class =====

class {Domain}Service:
    # Constructor with dependencies

    # ===== Public Methods (CRUD) =====
    async def create(...)
    async def get(...)
    async def list(...)
    async def update(...)
    async def delete(...)

    # ===== Public Methods (Business) =====
    # 도메인별 비즈니스 메서드

    # ===== Private Methods =====
    def _validate_*(...)
    def _can_*(...)
    async def _process_*(...)
```

## 체크리스트

- [ ] 스펙 4.1장 비즈니스 규칙 모두 구현됨
- [ ] 스펙 4.2장 검증 규칙 적용됨
- [ ] 스펙 5장 외부 연동 구현됨
- [ ] 스펙 6장 에러 코드에 맞는 예외 발생
- [ ] 의존성 주입 방식 사용 (테스트 용이)
- [ ] async/await 패턴 사용
- [ ] 상태 전이 검증 로직 있음 (해당시)
- [ ] 재시도/타임아웃 정책 적용됨 (해당시)
