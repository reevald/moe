"""
Health check endpoint.
"""

from fastapi import APIRouter, Depends
from redis import Redis

from api.dependencies import get_redis
from common.schemas import APIResponse, HealthData

router = APIRouter()


@router.get(
    "/health",
    response_model=APIResponse,
    tags=["Health"]
)
async def health_check(redis_client: Redis = Depends(get_redis)):
    """
    Health check endpoint.

    Returns:
        APIResponse: Health status of the service
    """
    try:
        # Check Redis connection
        redis_client.ping()
        status = "healthy"
    except Exception:
        status = "unhealthy"

    return APIResponse(
        success=True,
        data=HealthData(status=status).model_dump()
    )
