"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.router import router

app = FastAPI(
    title="RAG Product API",
    description="RAG system with Qdrant vector database",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
