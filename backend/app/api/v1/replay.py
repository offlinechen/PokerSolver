"""Replay API — GET hand replay data with street-by-street breakdown."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.config import settings
from app.schemas.replay import EquityPoint, ReplayResponse, StreetSnapshot

router = APIRouter(prefix="/hands", tags=["replay"])

STREET_ORDER = ["PREFLOP", "FLOP", "TURN", "RIVER"]


@router.get(
    "/{hand_id}/replay",
    response_model=ReplayResponse,
    summary="获取手牌回放数据",
)
async def get_hand_replay(
    hand_id: str,
    db: AsyncSession = Depends(get_db),
) -> ReplayResponse:
    """Get structured replay data for a hand."""
    if settings.fake_mode:
        raise HTTPException(status_code=404, detail="No DB in fake mode")

    from app.models.action import Action
    from app.models.hand import Hand
    from app.schemas.hand import HandActionResponse

    query = (
        select(Hand)
        .options(
            selectinload(Hand.actions).selectinload(Action.player),
            selectinload(Hand.players),
        )
        .where(Hand.id == hand_id)
    )
    result = await db.execute(query)
    hand = result.scalar_one_or_none()

    if hand is None:
        raise HTTPException(status_code=404, detail="Hand not found")

    # Sort actions by order
    sorted_actions = sorted(hand.actions, key=lambda a: a.action_order)

    # Build position map
    player_positions: dict[str, str] = {}
    player_types: dict[str, str] = {}
    for p in hand.players:
        player_positions[p.id] = p.position
        player_types[p.id] = "Hero" if p.position == hand.hero_position else "Villain"

    # Group actions by street
    street_actions: dict[str, list[HandActionResponse]] = {
        s: [] for s in STREET_ORDER
    }

    for a in sorted_actions:
        resp = HandActionResponse(
            street=a.street,
            player_position=player_positions.get(a.player_id, "Unknown"),
            player_type=player_types.get(a.player_id, "Villain"),
            action_type=a.action_type,
            amount=float(a.amount) if a.amount else None,
            action_order=a.action_order,
        )
        if a.street in street_actions:
            street_actions[a.street].append(resp)

    # Estimate pot progression
    starting_pot = float(hand.pot_size_bb)
    hero_stack = float(hand.stack_size_bb)

    # Parse board by street
    board_cards_str = hand.board_cards or ""
    board_by_street: dict[str, str | None] = {
        "PREFLOP": None,
        "FLOP": board_cards_str[:6] if len(board_cards_str) >= 6 else None,
        "TURN": board_cards_str[:8] if len(board_cards_str) >= 8 else None,
        "RIVER": board_cards_str[:11] if len(board_cards_str) >= 11 else None,
    }

    # Build street snapshots with pot progression
    streets: list[StreetSnapshot] = []
    running_pot = starting_pot
    running_stack = hero_stack

    for street in STREET_ORDER:
        street_acts = street_actions.get(street, [])
        if not street_acts:
            # Empty street (no actions recorded for this street)
            streets.append(
                StreetSnapshot(
                    street=street,
                    actions=[],
                    hero_cards=hand.hero_cards,
                    board_cards=board_by_street.get(street),
                    pot_size_bb=round(running_pot, 2),
                    hero_stack_bb=round(running_stack, 2),
                )
            )
            continue

        # Estimate pot growth from betting actions
        for act in street_acts:
            if act.action_type in ("BET", "RAISE", "CALL", "ALL_IN"):
                amt = act.amount or 0
                if act.player_type == "Hero" and act.action_type in (
                    "BET",
                    "RAISE",
                    "ALL_IN",
                ):
                    running_stack -= amt
                running_pot += amt

        streets.append(
            StreetSnapshot(
                street=street,
                actions=street_acts,
                hero_cards=hand.hero_cards,
                board_cards=board_by_street.get(street),
                pot_size_bb=round(running_pot, 2),
                hero_stack_bb=round(running_stack, 2),
            )
        )

    # Build equity curve (simplified estimation)
    equity_curve = _estimate_equity_curve(hand.hero_cards, board_cards_str, running_pot)

    return ReplayResponse(
        hand_id=hand.id,
        hero_cards=hand.hero_cards,
        hero_position=hand.hero_position,
        board_cards=hand.board_cards,
        final_pot_bb=round(running_pot, 2),
        result_bb=float(hand.result_bb) if hand.result_bb else None,
        streets=streets,
        equity_curve=equity_curve,
        total_actions=len(sorted_actions),
    )


def _estimate_equity_curve(
    hero_cards: str, board_cards: str, final_pot: float
) -> list[EquityPoint]:
    """Build estimated equity curve for visualization.

    Uses the equity_calculator to get real equity at each street.
    If solver is unavailable, returns fallback estimates.
    """
    try:
        from app.solver.equity_calculator import calculate_equity

        hero_cards_list = [hero_cards[0:2], hero_cards[2:4]] if len(hero_cards) >= 4 else []

        points: list[EquityPoint] = []

        # Preflop
        if hero_cards_list:
            eq = calculate_equity(
                hero_cards=hero_cards_list,
                board_cards=[],
                hero_position="BTN",
                simulations=2000,  # lighter sims for replay
            )
        else:
            eq = 50.0
        points.append(EquityPoint(label="Preflop", equity=round(eq, 1), pot_size_bb=final_pot * 0.15))

        # Flop (3 cards)
        if board_cards and len(board_cards) >= 6:
            flop_cards = [board_cards[0:2], board_cards[2:4], board_cards[4:6]]
            if hero_cards_list:
                eq = calculate_equity(
                    hero_cards=hero_cards_list,
                    board_cards=flop_cards,
                    hero_position="BTN",
                    simulations=2000,
                )
            points.append(EquityPoint(label="Flop", equity=round(eq, 1), pot_size_bb=final_pot * 0.35))

        # Turn (4 cards)
        if board_cards and len(board_cards) >= 8:
            turn_cards = [board_cards[i : i + 2] for i in range(0, 8, 2)]
            if hero_cards_list:
                eq = calculate_equity(
                    hero_cards=hero_cards_list,
                    board_cards=turn_cards,
                    hero_position="BTN",
                    simulations=2000,
                )
            points.append(EquityPoint(label="Turn", equity=round(eq, 1), pot_size_bb=final_pot * 0.65))

        # River (5 cards)
        if board_cards and len(board_cards) >= 11:
            river_cards = [board_cards[i : i + 2] for i in range(0, 10, 2)]
            if hero_cards_list:
                eq = calculate_equity(
                    hero_cards=hero_cards_list,
                    board_cards=river_cards,
                    hero_position="BTN",
                    simulations=2000,
                )
            points.append(EquityPoint(label="River", equity=round(eq, 1), pot_size_bb=final_pot))

        return points

    except Exception:
        # Fallback: simple linear estimation
        return [
            EquityPoint(label="Preflop", equity=55.0, pot_size_bb=final_pot * 0.1),
            EquityPoint(label="Flop", equity=60.0, pot_size_bb=final_pot * 0.35),
            EquityPoint(label="Turn", equity=50.0, pot_size_bb=final_pot * 0.65),
            EquityPoint(label="River", equity=45.0, pot_size_bb=final_pot),
        ]
