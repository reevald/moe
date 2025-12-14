"""
MOE API endpoints for problems and submissions.
"""

import json
import logging

from celery import Celery
from fastapi import APIRouter, Depends, HTTPException
from redis import Redis
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_redis, get_settings, verify_token
from common.config import Settings
from common.schemas import (
    APIResponse,
    ProblemData,
    SubmissionCreateData,
    SubmissionCreateRequest,
    SubmissionResultData,
    SubmissionResultDetail,
    SubmissionStatusData,
    LeanValidation,
)
from modules import moe_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/moe/problems/random",
    response_model=APIResponse,
    tags=["Problems"]
)
async def get_random_problem(
    _token: str = Depends(verify_token),
    settings: Settings = Depends(get_settings)
):
    """
    Get a random math problem.

    Returns:
        APIResponse: Random problem data
    """
    try:
        problem = moe_service.get_random_problem_from_supabase(
            settings.supabase_url,
            settings.supabase_secret_key
        )

        if not problem:
            raise HTTPException(
                status_code=404,
                detail="No problems available"
            )

        return APIResponse(
            success=True,
            data=ProblemData(
                problem_id=problem["problem_id"],
                statement_latex=problem["statement_latex"]
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch random problem: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/moe/problems/{problem_id}",
    response_model=APIResponse,
    tags=["Problems"]
)
async def get_problem_by_id(
    problem_id: str,
    _token: str = Depends(verify_token),
    settings: Settings = Depends(get_settings)
):
    """
    Get a specific problem by ID.

    Args:
        problem_id: Problem identifier

    Returns:
        APIResponse: Problem data
    """
    try:
        problem = moe_service.get_problem_by_id_from_supabase(
            problem_id,
            settings.supabase_url,
            settings.supabase_secret_key
        )

        if not problem:
            raise HTTPException(
                status_code=404,
                detail=f"Problem {problem_id} not found"
            )

        return APIResponse(
            success=True,
            data=ProblemData(
                problem_id=problem["problem_id"],
                statement_latex=problem["statement_latex"]
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch problem {problem_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post(
    "/moe/submissions",
    response_model=APIResponse,
    tags=["Submissions"]
)
async def create_submission(
    request: SubmissionCreateRequest,
    _token: str = Depends(verify_token),
    db: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings)
):
    """
    Submit a solution for evaluation.

    Args:
        request: Submission creation request

    Returns:
        APIResponse: Created submission data
    """
    try:
        # Create submission record
        submission = moe_service.create_submission(
            db,
            request.problem_id,
            request.solution_latex
        )

        # Create Celery client for task dispatching
        celery_client = Celery(
            broker=settings.redis_url,
            backend=settings.redis_url
        )

        # Dispatch Celery task for async processing
        celery_client.send_task(
            "worker.tasks.process_submission",
            args=[
                submission.submission_id,
                submission.problem_id,
                submission.submission_latex
            ]
        )

        logger.info(
            f"Dispatched processing task for submission "
            f"{submission.submission_id}"
        )

        return APIResponse(
            success=True,
            data=SubmissionCreateData(
                submission_id=submission.submission_id,
                problem_id=submission.problem_id,
                status=submission.status,
                submitted_at=submission.submitted_at
            ).model_dump()
        )
    except moe_service.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create submission: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/moe/submissions/{submission_id}/status",
    response_model=APIResponse,
    tags=["Submissions"]
)
async def get_submission_status(
    submission_id: str,
    _token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get submission status and progress.

    Args:
        submission_id: Submission identifier

    Returns:
        APIResponse: Submission status data
    """
    try:
        submission = moe_service.get_submission_by_id(
            db,
            submission_id
        )

        if not submission:
            raise HTTPException(
                status_code=404,
                detail=f"Submission {submission_id} not found"
            )

        return APIResponse(
            success=True,
            data=SubmissionStatusData(
                submission_id=submission.submission_id,
                problem_id=submission.problem_id,
                status=submission.status,
                submitted_at=submission.submitted_at,
                updated_at=submission.updated_at,
                progress=submission.progress
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch status for {submission_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.get(
    "/moe/submissions/{submission_id}/result",
    response_model=APIResponse,
    tags=["Submissions"]
)
async def get_submission_result(
    submission_id: str,
    _token: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get submission evaluation result.

    Args:
        submission_id: Submission identifier

    Returns:
        APIResponse: Submission result data
    """
    try:
        submission = moe_service.get_submission_by_id(
            db,
            submission_id
        )

        if not submission:
            raise HTTPException(
                status_code=404,
                detail=f"Submission {submission_id} not found"
            )

        result = moe_service.get_submission_result(db, submission_id)

        result_detail = None
        if result:
            result_detail = SubmissionResultDetail(
                verdict=result.verdict,
                lean_validation=LeanValidation(
                    is_valid=result.lean_is_valid,
                    status=result.lean_status,
                    errors=result.lean_errors or [],
                    remaining_goals=result.lean_remaining_goals or []
                ),
                feedback=result.feedback or []
            )

        return APIResponse(
            success=True,
            data=SubmissionResultData(
                submission_id=submission.submission_id,
                problem_id=submission.problem_id,
                status=submission.status,
                submitted_at=submission.submitted_at,
                evaluated_at=submission.evaluated_at,
                result=result_detail
            ).model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch result for {submission_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
