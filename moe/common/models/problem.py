"""
Problem model for storing math olympiad problems.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

if TYPE_CHECKING:
    from .submission import Submission


class Problem(Base):
    """
    Math problem entity.

    Stores problem statements in both LaTeX and Lean formats,
    along with state information for Lean verification.
    """

    __tablename__ = "problems"

    problem_id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        index=True
    )
    statement_latex: Mapped[str] = mapped_column(Text, nullable=False)
    statement_lean: Mapped[str] = mapped_column(Text, nullable=False)
    state_before_lean: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    state_after_lean: Mapped[str] = mapped_column(Text, nullable=False)
    tactic_lean: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
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

    # Relationships
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="problem",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Problem(problem_id={self.problem_id})>"
