"""API v1 main router."""

from fastapi import APIRouter
from .endpoints import request_forms, health

# Create main router for API v1
router = APIRouter()

# Include all endpoint routers
router.include_router(
    request_forms.router,
    prefix="/request-forms",
    tags=["request-forms"]
)



router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

 