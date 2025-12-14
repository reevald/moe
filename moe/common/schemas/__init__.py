"""
Pydantic schemas for API request and response models.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# Base response wrapper
class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Operation success status")
    data: Optional[dict[str, Any]] = Field(
        default=None,
        description="Response data"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if success=False"
    )


# Health check schemas
class HealthData(BaseModel):
    """Health check response data."""

    status: str = Field(..., description="Service health status")


# Problem schemas
class ProblemData(BaseModel):
    """Problem data for API responses."""

    problem_id: str = Field(..., description="Unique problem identifier")
    statement_latex: str = Field(
        ...,
        description="Problem statement in LaTeX format"
    )


# Submission schemas
class SubmissionCreateRequest(BaseModel):
    """Request body for creating a submission."""

    problem_id: str = Field(..., description="Problem ID to submit for")
    solution_latex: str = Field(
        ...,
        description="Solution in LaTeX format"
    )


class SubmissionCreateData(BaseModel):
    """Response data for submission creation."""

    submission_id: str = Field(
        ...,
        description="Unique submission identifier"
    )
    problem_id: str = Field(..., description="Associated problem ID")
    status: str = Field(
        ...,
        description="Submission status (pending/processing/completed)"
    )
    submitted_at: datetime = Field(..., description="Submission timestamp")


class SubmissionStatusData(BaseModel):
    """Response data for submission status check."""

    submission_id: str = Field(..., description="Submission identifier")
    problem_id: str = Field(..., description="Associated problem ID")
    status: str = Field(..., description="Current submission status")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    progress: int = Field(..., description="Progress percentage (0-100)")


# Submission result schemas
class LeanValidation(BaseModel):
    """Lean proof checker validation result."""

    is_valid: bool = Field(..., description="Validation result")
    status: str = Field(..., description="Validation status")
    errors: list[Any] = Field(
        default_factory=list,
        description="Validation errors"
    )
    remaining_goals: list[Any] = Field(
        default_factory=list,
        description="Remaining proof goals"
    )


class SubmissionResultDetail(BaseModel):
    """Detailed submission result information."""

    verdict: str = Field(..., description="Final verdict (accepted/rejected)")
    lean_validation: LeanValidation = Field(
        ...,
        description="Lean validation details"
    )
    feedback: list[str] = Field(
        ...,
        description="Human-readable feedback"
    )


class SubmissionResultData(BaseModel):
    """Response data for submission result."""

    submission_id: str = Field(..., description="Submission identifier")
    problem_id: str = Field(..., description="Associated problem ID")
    status: str = Field(..., description="Submission status")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    evaluated_at: Optional[datetime] = Field(
        default=None,
        description="Evaluation completion timestamp"
    )
    result: Optional[SubmissionResultDetail] = Field(
        default=None,
        description="Evaluation result details"
    )
