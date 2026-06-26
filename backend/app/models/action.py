"""Action model — every action taken in a hand."""

from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Action(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    hand_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hands.id"), nullable=False
    )
    player_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("players.id"), nullable=False
    )
    street: Mapped[str] = mapped_column(String(16), nullable=False)  # PREFLOP/FLOP/TURN/RIVER
    action_type: Mapped[str] = mapped_column(String(16), nullable=False)  # FOLD/CHECK/CALL/BET/RAISE/ALL_IN
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    action_order: Mapped[int] = mapped_column(Integer, nullable=False)

    hand = relationship("Hand", back_populates="actions")
    player = relationship("Player", back_populates="actions")
