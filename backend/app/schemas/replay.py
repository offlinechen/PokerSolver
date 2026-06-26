"""Pydantic schemas for hand replay."""
from pydantic import BaseModel

from app.schemas.hand import HandActionResponse


class StreetSnapshot(BaseModel):
    """Snapshot of hand state at a given street."""
    street: str
    actions: list[HandActionResponse]
    hero_cards: str
    board_cards: str | None
    pot_size_bb: float
    hero_stack_bb: float


class EquityPoint(BaseModel):
    """Equity data point for EV curve chart."""
    label: str  # e.g. "Preflop", "Flop", "Turn", "River"
    equity: float  # 0-100
    pot_size_bb: float


class ReplayResponse(BaseModel):
    """Full replay data for a hand."""
    hand_id: str
    hero_cards: str
    hero_position: str
    board_cards: str | None
    final_pot_bb: float
    result_bb: float | None
    streets: list[StreetSnapshot]
    equity_curve: list[EquityPoint]
    total_actions: int
