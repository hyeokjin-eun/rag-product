# Temporal 에이전트

워크플로우/액티비티 구현 가이드

## 작업 흐름

```
1. 워크플로우 요구사항 분석
   ↓
2. 액티비티 정의 (activities/)
   ↓
3. 워크플로우 정의 (workflows/)
   ↓
4. 워커에 등록 (main.py)
   ↓
5. 테스트 작성
```

## 파일 위치

| 구분 | 경로 |
|------|------|
| 워크플로우 | `workers/workflows/{name}_workflow.py` |
| 액티비티 | `workers/activities/{name}_activities.py` |
| 워커 진입점 | `workers/main.py` |

## 워크플로우 목록

| 워크플로우 | 역할 |
|------------|------|
| EmbeddingWorkflow | 문서 임베딩 처리 |
| IngestionWorkflow | 데이터 수집 파이프라인 |

## 구현 패턴

### 1. 액티비티 정의

```python
# workers/activities/embedding_activities.py
from temporalio import activity
from dataclasses import dataclass


@dataclass
class EmbedTextInput:
    text: str
    provider: str = "openai"


@dataclass
class EmbedTextOutput:
    embedding: list[float]
    dimension: int


@activity.defn
async def embed_text(input: EmbedTextInput) -> EmbedTextOutput:
    """텍스트를 벡터로 변환하는 액티비티"""
    from app.domains.embeddings.service import EmbeddingService, EmbeddingProviderType

    provider = EmbeddingService.create(EmbeddingProviderType(input.provider))
    embedding = await provider.embed_single(input.text)

    return EmbedTextOutput(
        embedding=embedding,
        dimension=provider.dimension,
    )


@activity.defn
async def chunk_document(document_id: str) -> list[str]:
    """문서를 청크로 분할하는 액티비티"""
    from app.domains.documents.service import DocumentService

    service = DocumentService()
    document = await service.get(document_id)
    return service._chunk_text(document.content)


@activity.defn
async def save_embeddings(
    document_id: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> bool:
    """임베딩을 Qdrant에 저장하는 액티비티"""
    from app.infrastructure.qdrant.client import QdrantClient

    client = QdrantClient()
    await client.upsert_vectors(
        collection="documents",
        ids=[f"{document_id}_{i}" for i in range(len(chunks))],
        vectors=embeddings,
        payloads=[{"document_id": document_id, "chunk": chunk} for chunk in chunks],
    )
    return True
```

### 2. 워크플로우 정의

```python
# workers/workflows/embedding_workflow.py
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy
from dataclasses import dataclass

with workflow.unsafe.imports_passed_through():
    from workers.activities.embedding_activities import (
        embed_text,
        chunk_document,
        save_embeddings,
        EmbedTextInput,
    )


@dataclass
class EmbeddingWorkflowInput:
    document_id: str
    provider: str = "openai"


@dataclass
class EmbeddingWorkflowOutput:
    document_id: str
    chunk_count: int
    success: bool


@workflow.defn
class EmbeddingWorkflow:
    """문서 임베딩 워크플로우"""

    @workflow.run
    async def run(self, input: EmbeddingWorkflowInput) -> EmbeddingWorkflowOutput:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_interval=timedelta(minutes=1),
            maximum_attempts=3,
        )

        # 1. 문서 청킹
        chunks = await workflow.execute_activity(
            chunk_document,
            input.document_id,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        # 2. 각 청크 임베딩
        embeddings = []
        for chunk in chunks:
            result = await workflow.execute_activity(
                embed_text,
                EmbedTextInput(text=chunk, provider=input.provider),
                start_to_close_timeout=timedelta(minutes=1),
                retry_policy=retry_policy,
            )
            embeddings.append(result.embedding)

        # 3. Qdrant에 저장
        await workflow.execute_activity(
            save_embeddings,
            args=[input.document_id, chunks, embeddings],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        return EmbeddingWorkflowOutput(
            document_id=input.document_id,
            chunk_count=len(chunks),
            success=True,
        )
```

### 3. 워커 등록

```python
# workers/main.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from workers.workflows.embedding_workflow import EmbeddingWorkflow
from workers.workflows.ingestion_workflow import IngestionWorkflow
from workers.activities.embedding_activities import (
    embed_text,
    chunk_document,
    save_embeddings,
)
from workers.activities.document_activities import (
    fetch_document,
    parse_document,
)


async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="rag-task-queue",
        workflows=[
            EmbeddingWorkflow,
            IngestionWorkflow,
        ],
        activities=[
            embed_text,
            chunk_document,
            save_embeddings,
            fetch_document,
            parse_document,
        ],
    )

    print("Worker started, listening on task queue: rag-task-queue")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
```

### 4. 워크플로우 실행 (API에서)

```python
# app/api/v1/documents.py
from temporalio.client import Client
from workers.workflows.embedding_workflow import (
    EmbeddingWorkflow,
    EmbeddingWorkflowInput,
)


@router.post("/{document_id}/embed")
async def start_embedding(document_id: str, provider: str = "openai"):
    client = await Client.connect("localhost:7233")

    handle = await client.start_workflow(
        EmbeddingWorkflow.run,
        EmbeddingWorkflowInput(document_id=document_id, provider=provider),
        id=f"embed-{document_id}",
        task_queue="rag-task-queue",
    )

    return {"workflow_id": handle.id, "status": "started"}
```

## 체크리스트

- [ ] 액티비티에 `@activity.defn` 데코레이터
- [ ] 워크플로우에 `@workflow.defn` 데코레이터
- [ ] Input/Output은 dataclass로 정의
- [ ] RetryPolicy 설정
- [ ] 적절한 timeout 설정
- [ ] 워커 main.py에 등록

## 주의사항

- 워크플로우 내에서 비결정적 코드 금지 (random, datetime.now 등)
- 외부 호출은 반드시 액티비티로 분리
- 액티비티는 멱등성 보장 권장
- 긴 작업은 heartbeat 사용

## 워커 실행

```bash
# 워커 실행 (별도 프로세스)
python -m workers.main

# 여러 워커로 수평 확장
python -m workers.main &
python -m workers.main &
python -m workers.main &
```
