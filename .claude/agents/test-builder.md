# Test Builder 에이전트

스펙 문서와 테스트 설계를 기반으로 테스트 코드를 작성합니다.

## 역할

- 단위 테스트 작성
- 통합 테스트 작성
- Fixture 생성
- Mock 설정

## 입력

- 스펙 문서 9장 "테스트 시나리오" (Test Designer 결과물)
- `schemas.py`, `service.py`, `api/v1/{domain}.py` (구현 코드)

## 출력

- `tests/unit/domains/test_{domain}.py`
- `tests/integration/test_{domain}_api.py`
- `tests/conftest.py` (공통 Fixture)

## 구현 프로세스

### 1. 스펙 분석

```
스펙 9장에서 추출:
├── 9.1 단위 테스트 케이스
├── 9.2 통합 테스트 시나리오
└── 9.3 장애 시나리오 테스트
```

### 2. 공통 Fixture 설정

```python
# tests/conftest.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app
from app.domains.{domain}.schemas import {Domain}Schema, {Domain}Status
from app.domains.{domain}.service import {Domain}Service
from app.domains.{domain}.repository import {Domain}Repository


# ===== App Fixtures =====

@pytest.fixture
def client():
    """동기 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ===== Mock Fixtures =====

@pytest.fixture
def mock_repository():
    """Repository Mock"""
    repo = MagicMock(spec={Domain}Repository)
    repo.save = AsyncMock(return_value=None)
    repo.find_by_id = AsyncMock(return_value=None)
    repo.find_all = AsyncMock(return_value=([], 0))
    repo.delete = AsyncMock(return_value=True)
    return repo


@pytest.fixture
def mock_qdrant():
    """Qdrant Client Mock"""
    client = MagicMock()
    client.search = AsyncMock(return_value=[])
    client.upsert = AsyncMock(return_value=True)
    return client


# ===== Data Fixtures =====

@pytest.fixture
def sample_{domain}():
    """샘플 엔티티"""
    return {Domain}Schema(
        id="test-uuid-001",
        title="테스트 문서",
        content="테스트 내용입니다.",
        status={Domain}Status.PENDING,
        metadata={},
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_{domain}_list(sample_{domain}):
    """샘플 엔티티 목록"""
    return [sample_{domain}] * 5


@pytest.fixture
def valid_create_request():
    """유효한 생성 요청"""
    return {
        "title": "테스트 제목",
        "content": "테스트 내용입니다.",
        "metadata": {"key": "value"},
    }


@pytest.fixture
def invalid_create_request():
    """잘못된 생성 요청"""
    return {
        "title": "",  # 빈 제목
        "content": None,
    }


# ===== Service Fixtures =====

@pytest.fixture
def {domain}_service(mock_repository):
    """Service 인스턴스 (Mock 주입)"""
    return {Domain}Service(repository=mock_repository)
```

### 3. 단위 테스트 작성

```python
# tests/unit/domains/test_{domain}.py

"""
{Domain} Service 단위 테스트

스펙 문서 9.1장 테스트 케이스 기반
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.domains.{domain}.service import {Domain}Service
from app.domains.{domain}.schemas import (
    {Domain}CreateRequest,
    {Domain}UpdateRequest,
    {Domain}Schema,
    {Domain}Status,
)
from app.core.exceptions import {Domain}NotFoundError, {Domain}ValidationError


class Test{Domain}ServiceCreate:
    """create() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_create_success_required_fields(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
    ):
        """성공: 필수 필드만으로 생성"""
        # Given
        request = {Domain}CreateRequest(
            title="테스트",
            content="테스트 내용",
        )

        # When
        result = await {domain}_service.create(request)

        # Then
        assert result.title == "테스트"
        assert result.status == {Domain}Status.PENDING
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_success_all_fields(
        self,
        {domain}_service: {Domain}Service,
    ):
        """성공: 모든 필드로 생성"""
        # Given
        request = {Domain}CreateRequest(
            title="테스트",
            content="테스트 내용",
            metadata={"author": "test"},
        )

        # When
        result = await {domain}_service.create(request)

        # Then
        assert result.title == "테스트"
        # metadata는 Response에 없으므로 내부 확인 필요

    @pytest.mark.asyncio
    async def test_create_generates_uuid(
        self,
        {domain}_service: {Domain}Service,
    ):
        """성공: UUID가 생성됨"""
        request = {Domain}CreateRequest(title="테스트", content="내용")

        result = await {domain}_service.create(request)

        assert result.id is not None
        assert len(result.id) == 36  # UUID 형식


class Test{Domain}ServiceGet:
    """get() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_get_success(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
        sample_{domain},
    ):
        """성공: 존재하는 문서 조회"""
        # Given
        mock_repository.find_by_id.return_value = sample_{domain}

        # When
        result = await {domain}_service.get("test-uuid-001")

        # Then
        assert result.id == "test-uuid-001"
        assert result.title == "테스트 문서"

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
    ):
        """실패: 존재하지 않는 문서"""
        # Given
        mock_repository.find_by_id.return_value = None

        # When & Then
        with pytest.raises({Domain}NotFoundError) as exc_info:
            await {domain}_service.get("non-existent")

        assert exc_info.value.code == "{DOMAIN}_NOT_FOUND"


class Test{Domain}ServiceList:
    """list() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_list_success(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
        sample_{domain}_list,
    ):
        """성공: 목록 조회"""
        # Given
        mock_repository.find_all.return_value = (sample_{domain}_list, 5)

        # When
        result = await {domain}_service.list(page=1, limit=20)

        # Then
        assert len(result.items) == 5
        assert result.total == 5
        assert result.page == 1

    @pytest.mark.asyncio
    async def test_list_empty(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
    ):
        """성공: 빈 목록"""
        # Given
        mock_repository.find_all.return_value = ([], 0)

        # When
        result = await {domain}_service.list()

        # Then
        assert len(result.items) == 0
        assert result.total == 0


class Test{Domain}ServiceUpdate:
    """update() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
        sample_{domain},
    ):
        """성공: 부분 수정"""
        # Given
        mock_repository.find_by_id.return_value = sample_{domain}
        request = {Domain}UpdateRequest(title="수정된 제목")

        # When
        result = await {domain}_service.update("test-uuid-001", request)

        # Then
        assert result.title == "수정된 제목"
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
    ):
        """실패: 존재하지 않는 문서 수정"""
        # Given
        mock_repository.find_by_id.return_value = None

        # When & Then
        with pytest.raises({Domain}NotFoundError):
            await {domain}_service.update(
                "non-existent",
                {Domain}UpdateRequest(title="수정"),
            )


class Test{Domain}ServiceDelete:
    """delete() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        {domain}_service: {Domain}Service,
        mock_repository,
        sample_{domain},
    ):
        """성공: 삭제"""
        # Given
        mock_repository.find_by_id.return_value = sample_{domain}
        mock_repository.delete.return_value = True

        # When
        result = await {domain}_service.delete("test-uuid-001")

        # Then
        assert result is True
        mock_repository.delete.assert_called_once_with("test-uuid-001")
```

### 4. 통합 테스트 작성

```python
# tests/integration/test_{domain}_api.py

"""
{Domain} API 통합 테스트

스펙 문서 9.2장 테스트 시나리오 기반
"""

import pytest
from httpx import AsyncClient


class Test{Domain}API:
    """API 엔드포인트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        async_client: AsyncClient,
        valid_create_request,
    ):
        """POST /{domain}s - 201 생성 성공"""
        response = await async_client.post(
            "/api/v1/{domain}s",
            json=valid_create_request,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == valid_create_request["title"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_validation_error(
        self,
        async_client: AsyncClient,
        invalid_create_request,
    ):
        """POST /{domain}s - 400 검증 실패"""
        response = await async_client.post(
            "/api/v1/{domain}s",
            json=invalid_create_request,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_success(
        self,
        async_client: AsyncClient,
        valid_create_request,
    ):
        """GET /{domain}s/{id} - 200 조회 성공"""
        # Given: 먼저 생성
        create_response = await async_client.post(
            "/api/v1/{domain}s",
            json=valid_create_request,
        )
        created_id = create_response.json()["id"]

        # When
        response = await async_client.get(f"/api/v1/{domain}s/{created_id}")

        # Then
        assert response.status_code == 200
        assert response.json()["id"] == created_id

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        async_client: AsyncClient,
    ):
        """GET /{domain}s/{id} - 404 없음"""
        response = await async_client.get("/api/v1/{domain}s/non-existent-id")

        assert response.status_code == 404
        assert response.json()["code"] == "{DOMAIN}_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_success(
        self,
        async_client: AsyncClient,
    ):
        """GET /{domain}s - 200 목록 조회"""
        response = await async_client.get("/api/v1/{domain}s")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_list_pagination(
        self,
        async_client: AsyncClient,
    ):
        """GET /{domain}s?page=1&limit=10 - 페이지네이션"""
        response = await async_client.get(
            "/api/v1/{domain}s",
            params={"page": 1, "limit": 10},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10

    @pytest.mark.asyncio
    async def test_update_success(
        self,
        async_client: AsyncClient,
        valid_create_request,
    ):
        """PATCH /{domain}s/{id} - 200 수정 성공"""
        # Given
        create_response = await async_client.post(
            "/api/v1/{domain}s",
            json=valid_create_request,
        )
        created_id = create_response.json()["id"]

        # When
        response = await async_client.patch(
            f"/api/v1/{domain}s/{created_id}",
            json={"title": "수정된 제목"},
        )

        # Then
        assert response.status_code == 200
        assert response.json()["title"] == "수정된 제목"

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        async_client: AsyncClient,
        valid_create_request,
    ):
        """DELETE /{domain}s/{id} - 204 삭제 성공"""
        # Given
        create_response = await async_client.post(
            "/api/v1/{domain}s",
            json=valid_create_request,
        )
        created_id = create_response.json()["id"]

        # When
        response = await async_client.delete(f"/api/v1/{domain}s/{created_id}")

        # Then
        assert response.status_code == 204

        # Verify deleted
        get_response = await async_client.get(f"/api/v1/{domain}s/{created_id}")
        assert get_response.status_code == 404


class Test{Domain}APILifecycle:
    """전체 생명주기 테스트"""

    @pytest.mark.asyncio
    async def test_full_lifecycle(
        self,
        async_client: AsyncClient,
    ):
        """CRUD 전체 흐름"""
        # 1. Create
        create_res = await async_client.post(
            "/api/v1/{domain}s",
            json={"title": "테스트", "content": "내용"},
        )
        assert create_res.status_code == 201
        id = create_res.json()["id"]

        # 2. Read
        get_res = await async_client.get(f"/api/v1/{domain}s/{id}")
        assert get_res.status_code == 200

        # 3. Update
        update_res = await async_client.patch(
            f"/api/v1/{domain}s/{id}",
            json={"title": "수정됨"},
        )
        assert update_res.status_code == 200
        assert update_res.json()["title"] == "수정됨"

        # 4. Delete
        delete_res = await async_client.delete(f"/api/v1/{domain}s/{id}")
        assert delete_res.status_code == 204

        # 5. Verify deleted
        verify_res = await async_client.get(f"/api/v1/{domain}s/{id}")
        assert verify_res.status_code == 404
```

### 5. 장애 시나리오 테스트

```python
# tests/integration/test_{domain}_failures.py

"""
{Domain} 장애 시나리오 테스트

스펙 문서 9.3장 기반
"""

import pytest
from unittest.mock import patch, AsyncMock


class Test{Domain}FailureScenarios:
    """장애 상황 테스트"""

    @pytest.mark.asyncio
    async def test_qdrant_connection_failure(
        self,
        async_client: AsyncClient,
    ):
        """Qdrant 연결 실패 시 적절한 에러 응답"""
        with patch(
            "app.infrastructure.qdrant.client.QdrantClient.search",
            side_effect=ConnectionError("Connection refused"),
        ):
            response = await async_client.get("/api/v1/{domain}s/search?q=test")

            assert response.status_code == 503
            assert "service unavailable" in response.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self,
        async_client: AsyncClient,
    ):
        """타임아웃 시 적절한 에러 응답"""
        with patch(
            "app.domains.{domain}.service.{Domain}Service.process",
            side_effect=TimeoutError("Request timeout"),
        ):
            response = await async_client.post(
                "/api/v1/{domain}s/test-id/process",
            )

            assert response.status_code in [408, 504]
```

## 출력 파일 구조

```
tests/
├── conftest.py                         # 공통 Fixture
├── unit/
│   └── domains/
│       └── test_{domain}.py            # 서비스 단위 테스트
└── integration/
    ├── test_{domain}_api.py            # API 통합 테스트
    └── test_{domain}_failures.py       # 장애 시나리오 테스트
```

## 체크리스트

- [ ] 스펙 9.1장 단위 테스트 케이스 모두 구현됨
- [ ] 스펙 9.2장 통합 테스트 시나리오 모두 구현됨
- [ ] 스펙 9.3장 장애 시나리오 테스트 구현됨
- [ ] 공통 Fixture conftest.py에 정의됨
- [ ] Mock으로 외부 의존성 격리됨
- [ ] @pytest.mark.asyncio 데코레이터 적용됨
- [ ] Given-When-Then 패턴 사용됨
- [ ] 테스트 이름이 테스트 내용을 설명함
