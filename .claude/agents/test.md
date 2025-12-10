# 테스트 에이전트

테스트 코드 작성 가이드

## 작업 흐름

```
1. 테스트 대상 분석
   ↓
2. 테스트 케이스 설계
   ↓
3. fixture 작성 (conftest.py)
   ↓
4. 테스트 코드 작성
   ↓
5. 실행 및 검증
```

## 파일 위치

| 구분 | 경로 |
|------|------|
| 설정 | `tests/conftest.py` |
| 단위 테스트 | `tests/unit/{domain}/test_{module}.py` |
| 통합 테스트 | `tests/integration/test_{feature}.py` |

## 테스트 구조

```
tests/
├── conftest.py              # 공통 fixture
├── unit/
│   ├── domains/
│   │   ├── test_documents.py
│   │   ├── test_embeddings.py
│   │   └── test_search.py
│   └── api/
│       └── test_routes.py
└── integration/
    ├── test_embedding_flow.py
    └── test_rag_pipeline.py
```

## 구현 패턴

### 1. conftest.py (공통 fixture)

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.domains.embeddings.base import EmbeddingProvider


@pytest.fixture
def client():
    """동기 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """비동기 테스트 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_embedding_provider():
    """임베딩 프로바이더 Mock"""
    provider = MagicMock(spec=EmbeddingProvider)
    provider.dimension = 1536
    provider.model_name = "test-model"
    provider.embed = AsyncMock(return_value=[[0.1] * 1536])
    provider.embed_single = AsyncMock(return_value=[0.1] * 1536)
    return provider


@pytest.fixture
def mock_qdrant_client():
    """Qdrant 클라이언트 Mock"""
    client = MagicMock()
    client.upsert = AsyncMock(return_value=True)
    client.search = AsyncMock(return_value=[])
    client.get = AsyncMock(return_value=None)
    return client


@pytest.fixture
def sample_document():
    """샘플 문서 데이터"""
    return {
        "id": "test-doc-001",
        "title": "Test Document",
        "content": "This is a test document content.",
        "metadata": {"source": "test"},
    }
```

### 2. 단위 테스트 - 서비스

```python
# tests/unit/domains/test_documents.py
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.documents.service import DocumentService
from app.domains.documents.schemas import DocumentUploadRequest


class TestDocumentService:
    """DocumentService 테스트"""

    @pytest.fixture
    def service(self, mock_qdrant_client):
        return DocumentService(qdrant=mock_qdrant_client)

    @pytest.mark.asyncio
    async def test_upload_creates_document(self, service):
        """문서 업로드 시 문서가 생성되어야 함"""
        request = DocumentUploadRequest(
            title="Test",
            content="Test content",
        )

        result = await service.upload(request)

        assert result.title == "Test"
        assert result.id is not None
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_upload_chunks_content(self, service):
        """긴 문서는 청킹되어야 함"""
        long_content = "a" * 1500  # chunk_size(500)보다 긴 텍스트
        request = DocumentUploadRequest(
            title="Long Doc",
            content=long_content,
        )

        with patch.object(service, '_chunk_text', wraps=service._chunk_text) as mock_chunk:
            await service.upload(request)
            mock_chunk.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing(self, service, mock_qdrant_client):
        """존재하지 않는 문서 조회 시 None 반환"""
        mock_qdrant_client.get.return_value = None

        result = await service.get("non-existent-id")

        assert result is None
```

### 3. 단위 테스트 - 임베딩

```python
# tests/unit/domains/test_embeddings.py
import pytest
from unittest.mock import AsyncMock, patch

from app.domains.embeddings.service import EmbeddingService, EmbeddingProviderType


class TestEmbeddingService:
    """EmbeddingService 테스트"""

    def test_create_openai_provider(self):
        """OpenAI 프로바이더 생성"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            provider = EmbeddingService.create(EmbeddingProviderType.OPENAI)
            assert provider.model_name.startswith("openai/")

    def test_create_unknown_provider_raises(self):
        """알 수 없는 프로바이더는 에러"""
        with pytest.raises(ValueError, match="Unknown provider"):
            EmbeddingService.create("unknown")

    def test_register_custom_provider(self, mock_embedding_provider):
        """커스텀 프로바이더 등록"""
        EmbeddingService.register("custom", type(mock_embedding_provider))
        assert "custom" in EmbeddingService._providers
```

### 4. 통합 테스트 - API

```python
# tests/integration/test_api.py
import pytest
from httpx import AsyncClient


class TestDocumentsAPI:
    """Documents API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_upload_document(self, async_client: AsyncClient):
        """POST /api/v1/documents"""
        response = await async_client.post(
            "/api/v1/documents",
            json={
                "title": "Test Document",
                "content": "This is test content.",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Document"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, async_client: AsyncClient):
        """GET /api/v1/documents/{id} - 404"""
        response = await async_client.get("/api/v1/documents/non-existent")

        assert response.status_code == 404
```

### 5. Temporal 워크플로우 테스트

```python
# tests/unit/workers/test_embedding_workflow.py
import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from workers.workflows.embedding_workflow import (
    EmbeddingWorkflow,
    EmbeddingWorkflowInput,
)
from workers.activities.embedding_activities import (
    embed_text,
    chunk_document,
    save_embeddings,
)


class TestEmbeddingWorkflow:
    """EmbeddingWorkflow 테스트"""

    @pytest.mark.asyncio
    async def test_workflow_completes(self):
        """워크플로우가 정상 완료되어야 함"""
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-queue",
                workflows=[EmbeddingWorkflow],
                activities=[embed_text, chunk_document, save_embeddings],
            ):
                result = await env.client.execute_workflow(
                    EmbeddingWorkflow.run,
                    EmbeddingWorkflowInput(document_id="test-doc"),
                    id="test-workflow",
                    task_queue="test-queue",
                )

                assert result.success is True
                assert result.document_id == "test-doc"
```

## 실행 명령

```bash
# 전체 테스트
pytest

# 단위 테스트만
pytest tests/unit

# 특정 파일
pytest tests/unit/domains/test_documents.py

# 커버리지 포함
pytest --cov=app --cov-report=html

# 비동기 테스트 (verbose)
pytest -v --asyncio-mode=auto
```

## 체크리스트

- [ ] pytest.fixture로 공통 설정 분리
- [ ] Mock으로 외부 의존성 격리
- [ ] `@pytest.mark.asyncio` async 테스트에 적용
- [ ] 성공/실패 케이스 모두 테스트
- [ ] 에러 메시지 검증

## 주의사항

- 외부 서비스(Qdrant, OpenAI 등)는 Mock 사용
- 통합 테스트는 실제 환경 필요 시 별도 마킹
- 테스트 데이터는 fixture로 관리
