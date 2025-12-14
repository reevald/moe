"""
Submission result model for storing evaluation results.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .submission import Submission


class SubmissionResult(Base):
    """
    Submission result entity.

    Stores evaluation results including verdict, Lean validation
    details, and feedback.
    """

    __tablename__ = "submission_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    submission_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("submissions.submission_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )

    verdict: Mapped[str] = mapped_column(String(20), nullable=False)
    lean_is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    lean_status: Mapped[str] = mapped_column(String(20), nullable=False)
    lean_errors: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    lean_remaining_goals: Mapped[Optional[dict[str, Any]]] = (
        mapped_column(JSON, nullable=True)
    )
    feedback: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    submission: Mapped["Submission"] = relationship(
        "Submission",
        back_populates="result"
    )

    def __repr__(self) -> str:
        return (
            f"<SubmissionResult(id={self.id}, "
            f"submission_id={self.submission_id}, "
            f"verdict={self.verdict})>"
        )
