"""Player model — a player in a specific hand."""

from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    hand_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hands.id"), nullable=False
    )
    seat_number: Mapped[int] = mapped_column(Integer, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(128), nullable=True)
    player_type: Mapped[str] = mapped_column(String(16), default="Villain")  # Hero | Villain
    position: Mapped[str] = mapped_column(String(16), nullable=False)
    stack_size_bb: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    hand = relationship("Hand", back_populates="players")
    actions = relationship("Action", back_populates="player")
