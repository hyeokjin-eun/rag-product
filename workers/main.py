"""Temporal worker entry point."""

import asyncio

from temporalio.client import Client
from temporalio.worker import Worker

from app.core.config import settings
from workers.activities.health import health_check

# TODO: Import workflows and activities
# from workers.workflows.embedding_workflow import EmbeddingWorkflow
# from workers.workflows.ingestion_workflow import IngestionWorkflow
# from workers.activities.embedding_activities import embed_text, chunk_document
# from workers.activities.document_activities import fetch_document, parse_document

TASK_QUEUE = "rag-task-queue"


async def main() -> None:
    """Run the Temporal worker."""
    temporal_address = f"{settings.temporal_host}:{settings.temporal_port}"
    client = await Client.connect(temporal_address)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            # EmbeddingWorkflow,
            # IngestionWorkflow,
        ],
        activities=[
            health_check,
            # embed_text,
            # chunk_document,
            # fetch_document,
            # parse_document,
        ],
    )

    print(f"Worker started, listening on task queue: {TASK_QUEUE}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
