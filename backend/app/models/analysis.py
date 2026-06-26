"""Analysis model — stores Solver + AI analysis results for a hand."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    hand_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), ForeignKey("hands.id"), nullable=False
    )
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    equity: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    call_ev: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    raise_ev: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    fold_ev: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    strategy: Mapped[str | None] = mapped_column(String(256), nullable=True)  # JSON string
    gto_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    exploit_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_points: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    hand = relationship("Hand", back_populates="analyses")
