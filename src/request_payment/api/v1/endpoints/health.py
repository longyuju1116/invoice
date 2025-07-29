"""Health check API endpoints."""

from datetime import datetime
from fastapi import APIRouter, status

from ....models.schemas import HealthResponse

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check the health status of the application.",
)
async def health_check() -> HealthResponse:
    """Perform a basic health check.
    
    Returns:
        HealthResponse: The health status.
    """
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.utcnow()
    )


 