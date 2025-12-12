"""Health check activity."""

from temporalio import activity


@activity.defn
async def health_check() -> str:
    """Simple health check activity."""
    return "ok"
