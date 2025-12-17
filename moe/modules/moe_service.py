"""
MOE Business Logic Module.

This module contains pure business logic with NO framework dependencies.
Can be used by both API and Worker services.
"""

import json
import logging
import random
import time
import uuid
from datetime import datetime
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from common.models import Problem, Submission, SubmissionResult

logger = logging.getLogger(__name__)

# Cache the count for 5 minutes to avoid the HEAD request every time
_count_cache = {"count": 0, "timestamp": 0}
_CACHE_TTL = 300  # 5 minutes


class ProblemNotFoundError(Exception):
    """Raised when a problem is not found."""

    pass


class SubmissionNotFoundError(Exception):
    """Raised when a submission is not found."""

    pass


class ValidationError(Exception):
    """Raised when validation fails."""

    pass


def generate_problem_id() -> str:
    """Generate unique problem ID."""
    return f"moe-{uuid.uuid4().hex[:8]}"


def generate_submission_id() -> str:
    """Generate unique submission ID."""
    return f"sub-{uuid.uuid4().hex[:8]}"


def get_random_problem_from_supabase(
    supabase_url: str,
    supabase_secret_key: str
) -> Optional[dict[str, Any]]:
    """
    Fetch a random problem from Supabase.

    Args:
        supabase_url: Supabase REST API URL
        supabase_secret_key: Supabase service role secret key

    Returns:
        Problem data dictionary or None if no problems exist

    Raises:
        httpx.HTTPError: If API request fails
    """
    headers = {
        "apikey": supabase_secret_key,
        "Authorization": f"Bearer {supabase_secret_key}",
        "Content-Type": "application/json"
    }

    with httpx.Client() as client:
        # Use cached count if available and fresh
        now = time.time()
        if now - _count_cache["timestamp"] > _CACHE_TTL:
            # Refresh count
            count_response = client.head(
                f"{supabase_url}/problems",
                headers={**headers, "Prefer": "count=exact"}
            )
            count_response.raise_for_status()
            
            content_range = count_response.headers.get("Content-Range", "")
            if not content_range or "/" not in content_range:
                return None
            
            _count_cache["count"] = int(content_range.split("/")[1])
            _count_cache["timestamp"] = now
        
        total_count = _count_cache["count"]
        
        if total_count == 0:
            return None
        
        # Fetch random row
        random_offset = random.randint(0, total_count - 1)
        
        response = client.get(
            f"{supabase_url}/problems",
            headers={**headers, "Prefer": "count=none"},
            params={
                "limit": "1",
                "offset": str(random_offset)
            }
        )
        response.raise_for_status()
        problems = response.json()
        
        return problems[0] if problems else None


def get_problem_by_id_from_supabase(
    problem_id: str,
    supabase_url: str,
    supabase_secret_key: str
) -> Optional[dict[str, Any]]:
    """
    Fetch a specific problem from Supabase.

    Args:
        problem_id: Problem identifier
        supabase_url: Supabase REST API URL
        supabase_secret_key: Supabase service role secret key

    Returns:
        Problem data dictionary or None if not found

    Raises:
        httpx.HTTPError: If API request fails
    """
    headers = {
        "apikey": supabase_secret_key,
        "Authorization": f"Bearer {supabase_secret_key}",
        "Content-Type": "application/json"
    }

    with httpx.Client() as client:
        response = client.get(
            f"{supabase_url}/problems",
            headers=headers,
            params={"problem_id": f"eq.{problem_id}"}
        )
        response.raise_for_status()
        problems = response.json()

        if not problems:
            return None

        return problems[0]


def create_submission(
    db: Session,
    problem_id: str,
    solution_latex: str
) -> Submission:
    """
    Create a new submission record.

    Args:
        db: Database session
        problem_id: Problem identifier
        solution_latex: Solution in LaTeX format

    Returns:
        Created submission instance

    Raises:
        ValidationError: If problem_id is invalid
    """
    # Validate problem exists
    problem = db.query(Problem).filter(
        Problem.problem_id == problem_id
    ).first()

    if not problem:
        raise ValidationError(f"Problem {problem_id} not found")

    # Create submission
    submission_id = generate_submission_id()
    submission = Submission(
        submission_id=submission_id,
        problem_id=problem_id,
        submission_latex=solution_latex,
        status="pending",
        progress=0
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    logger.info(f"Created submission {submission_id} for {problem_id}")
    return submission


def get_submission_by_id(
    db: Session,
    submission_id: str
) -> Optional[Submission]:
    """
    Retrieve submission by ID.

    Args:
        db: Database session
        submission_id: Submission identifier

    Returns:
        Submission instance or None
    """
    return db.query(Submission).filter(
        Submission.submission_id == submission_id
    ).first()


def update_submission_status(
    db: Session,
    submission_id: str,
    status: str,
    progress: int
) -> None:
    """
    Update submission status and progress.

    Args:
        db: Database session
        submission_id: Submission identifier
        status: New status value
        progress: Progress percentage (0-100)

    Raises:
        SubmissionNotFoundError: If submission doesn't exist
    """
    submission = get_submission_by_id(db, submission_id)

    if not submission:
        raise SubmissionNotFoundError(
            f"Submission {submission_id} not found"
        )

    submission.status = status
    submission.progress = progress
    submission.updated_at = datetime.utcnow()

    if status == "completed":
        submission.evaluated_at = datetime.utcnow()

    db.commit()
    logger.info(
        f"Updated submission {submission_id}: "
        f"{status} ({progress}%)"
    )


def create_submission_result(
    db: Session,
    submission_id: str,
    verdict: str,
    lean_is_valid: bool,
    lean_status: str,
    lean_errors: Optional[list[Any]],
    lean_remaining_goals: Optional[list[Any]],
    feedback: Optional[list[str]]
) -> SubmissionResult:
    """
    Create submission result record.

    Args:
        db: Database session
        submission_id: Submission identifier
        verdict: Final verdict
        lean_is_valid: Lean validation result
        lean_status: Lean validation status
        lean_errors: Validation errors
        lean_remaining_goals: Remaining proof goals
        feedback: Human-readable feedback

    Returns:
        Created submission result instance

    Raises:
        SubmissionNotFoundError: If submission doesn't exist
    """
    submission = get_submission_by_id(db, submission_id)

    if not submission:
        raise SubmissionNotFoundError(
            f"Submission {submission_id} not found"
        )

    result = SubmissionResult(
        submission_id=submission_id,
        verdict=verdict,
        lean_is_valid=lean_is_valid,
        lean_status=lean_status,
        lean_errors=lean_errors,
        lean_remaining_goals=lean_remaining_goals,
        feedback=feedback
    )

    db.add(result)
    db.commit()
    db.refresh(result)

    logger.info(
        f"Created result for submission {submission_id}: "
        f"{verdict}"
    )
    return result


def get_submission_result(
    db: Session,
    submission_id: str
) -> Optional[SubmissionResult]:
    """
    Retrieve submission result by submission ID.

    Args:
        db: Database session
        submission_id: Submission identifier

    Returns:
        SubmissionResult instance or None
    """
    return db.query(SubmissionResult).filter(
        SubmissionResult.submission_id == submission_id
    ).first()
