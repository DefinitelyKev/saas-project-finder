from fastapi import APIRouter, Depends, HTTPException
import structlog

from src.api.v1.schemas import JobStatusResponse
from src.api.v1.dependencies import get_current_tenant
from src.domain.entities.tenant import Tenant

router = APIRouter()
logger = structlog.get_logger()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    tenant: Tenant = Depends(get_current_tenant),
) -> JobStatusResponse:
    """Get status of an async job."""

    try:
        # TODO: Get job status from database or cache
        # For now, return a mock response

        logger.info("Job status requested",
                   job_id=job_id,
                   tenant_id=str(tenant.id))

        return JobStatusResponse(
            job_id=job_id,
            status="completed",
            result={
                "content": "Mock job result",
                "usage": {"total_tokens": 150}
            },
            error_message=None,
            created_at=tenant.created_at.isoformat(),
            completed_at=tenant.created_at.isoformat(),
            progress_percentage=100,
        )

    except Exception as e:
        logger.error("Failed to get job status", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail="Internal server error")