"""Hands API — GET hands list, GET hand detail.

In FAKE_MODE: returns empty data (no DB needed).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.schemas.hand import HandListResponse, HandResponse

router = APIRouter(prefix="/hands", tags=["hands"])


@router.get(
    "",
    response_model=HandListResponse,
    summary="获取手牌历史列表",
)
async def list_hands(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
) -> HandListResponse:
    if settings.fake_mode:
        return HandListResponse(items=[], total=0, page=1, page_size=20)

    from sqlalchemy import func, select
    from app.models.hand import Hand
    from app.schemas.hand import HandListItem

    total_query = select(func.count(Hand.id))
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    query = (
        select(Hand)
        .order_by(Hand.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    hands = result.scalars().all()

    items = [
        HandListItem(
            id=h.id, hero_cards=h.hero_cards, board_cards=h.board_cards,
            hero_position=h.hero_position, result_bb=h.result_bb, created_at=h.created_at,
        )
        for h in hands
    ]
    return HandListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get(
    "/{hand_id}",
    response_model=HandResponse,
    summary="获取手牌详情",
)
async def get_hand(
    hand_id: str,
    db: AsyncSession = Depends(get_db),
) -> HandResponse:
    if settings.fake_mode:
        raise HTTPException(status_code=404, detail="No DB in fake mode")

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.hand import Hand
    from app.schemas.hand import HandActionResponse

    query = (
        select(Hand)
        .options(selectinload(Hand.actions), selectinload(Hand.players))
        .where(Hand.id == hand_id)
    )
    result = await db.execute(query)
    hand = result.scalar_one_or_none()

    if hand is None:
        raise HTTPException(status_code=404, detail="Hand not found")

    player_positions: dict[str, str] = {}
    for p in hand.players:
        player_positions[p.id] = p.position

    actions = [
        HandActionResponse(
            street=a.street,
            player_position=player_positions.get(a.player_id, "Unknown"),
            player_type="Hero" if player_positions.get(a.player_id) == hand.hero_position else "Villain",
            action_type=a.action_type,
            amount=float(a.amount) if a.amount else None,
            action_order=a.action_order,
        )
        for a in sorted(hand.actions, key=lambda a: a.action_order)
    ]

    return HandResponse(
        id=hand.id, hero_cards=hand.hero_cards, board_cards=hand.board_cards,
        hero_position=hand.hero_position,
        stack_size_bb=float(hand.stack_size_bb), pot_size_bb=float(hand.pot_size_bb),
        result_bb=float(hand.result_bb) if hand.result_bb else None,
        actions=actions, created_at=hand.created_at,
    )
