"""Hand model — core entity, one hand per record."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Hand(Base):
    __tablename__ = "hands"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    session_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("sessions.id"), nullable=True
    )
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    hero_position: Mapped[str] = mapped_column(String(16), nullable=False)
    hero_cards: Mapped[str] = mapped_column(String(16), nullable=False)  # e.g. "AhKh"
    board_cards: Mapped[str | None] = mapped_column(String(32), nullable=True)  # e.g. "AdTc3hKd2s"
    stack_size_bb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    pot_size_bb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    result_bb: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session = relationship("Session", back_populates="hands")
    user = relationship("User", back_populates="hands")
    players = relationship("Player", back_populates="hand", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="hand", cascade="all, delete-orphan")
    analyses = relationship("Analysis", back_populates="hand", cascade="all, delete-orphan")
