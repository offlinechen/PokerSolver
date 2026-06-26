"""Pydantic schemas for hand-related API responses."""

from datetime import datetime

from pydantic import BaseModel


class HandActionResponse(BaseModel):
    """Action in a hand response."""
    street: str
    player_position: str
    player_type: str  # Hero/Villain
    action_type: str
    amount: float | None
    action_order: int


class HandResponse(BaseModel):
    """Single hand response."""
    id: str
    hero_cards: str
    board_cards: str | None
    hero_position: str
    stack_size_bb: float
    pot_size_bb: float
    result_bb: float | None
    actions: list[HandActionResponse] = []
    created_at: datetime


class HandListItem(BaseModel):
    """Hand item in list view (abbreviated)."""
    id: str
    hero_cards: str
    board_cards: str | None
    hero_position: str
    result_bb: float | None
    created_at: datetime


class HandListResponse(BaseModel):
    """Paginated list of hands."""
    items: list[HandListItem]
    total: int
    page: int
    page_size: int
