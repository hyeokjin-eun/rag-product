"""API router configuration."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# TODO: Include domain routers here
# from app.api.v1 import documents, search, collections
# router.include_router(documents.router, prefix="/documents", tags=["documents"])
# router.include_router(search.router, prefix="/search", tags=["search"])
# router.include_router(collections.router, prefix="/collections", tags=["collections"])
