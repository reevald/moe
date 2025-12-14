"""
API v1 router aggregation.
"""

from fastapi import APIRouter

from .endpoints import health, moe

api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(health.router, prefix="", tags=["Health"])
api_router.include_router(moe.router, prefix="", tags=["MOE"])
