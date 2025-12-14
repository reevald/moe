"""
Submission model for storing user problem submissions.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .problem import Problem
    from .submission_result import SubmissionResult


class Submission(Base):
    """
    Submission entity for tracking user problem submissions.

    Stores submission data, status, and progress information.
    """

    __tablename__ = "submissions"

    submission_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        index=True
    )
    problem_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("problems.problem_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    submission_latex: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending"
    )
    progress: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    problem: Mapped["Problem"] = relationship(
        "Problem",
        back_populates="submissions"
    )
    result: Mapped[Optional["SubmissionResult"]] = relationship(
        "SubmissionResult",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Submission(submission_id={self.submission_id}, "
            f"status={self.status})>"
        )
