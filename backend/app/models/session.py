"""Session model — one gaming session contains many hands."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )
    platform: Mapped[str | None] = mapped_column(String(64), nullable=True)
    game_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    stake: Mapped[str | None] = mapped_column(String(32), nullable=True)
    buy_in: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cash_out: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user = relationship("User", back_populates="sessions")
    hands = relationship("Hand", back_populates="session")
