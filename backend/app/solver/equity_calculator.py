"""Poker equity engine — Monte Carlo hand evaluation and equity calculation.

Refactored to support multiple game modes via pluggable DeckConfig and HandEvaluator.

Modes: standard, shortdeck, sng, squid
- sng and squid currently use standard deck (ICM/survival EV to be added in M2)
"""

import random
from typing import Callable

from app.solver.engine.deck import DeckConfig, get_deck_config
from app.solver.engine.hand_evaluator import HandEvaluator
from app.solver.ranges.standard import STANDARD_RANGES
from app.solver.ranges.shortdeck import SHORTDECK_RANGES


def _generate_range(
    position: str,
    board_known: set[int],
    deck_config: DeckConfig,
) -> list[list[int]]:
    """Generate villain hole card pairs for a given position and deck.

    Uses mode-specific range tables. Falls back to BTN range for unknown positions.
    """
    mode = deck_config.mode
    ranges = STANDARD_RANGES if mode == "standard" else SHORTDECK_RANGES
    range_spec = ranges.get(position.upper(), ranges.get("BTN", []))

    result: list[list[int]] = []
    for (r1, r2), suited in range_spec:
        # Skip if either rank isn't valid for this deck
        if not deck_config.is_valid_rank(r1) or not deck_config.is_valid_rank(r2):
            continue

        if r1 == r2:  # Pocket pair
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in board_known:
                    continue
                for s2 in range(s1 + 1, 4):
                    c2 = r2 * 4 + s2
                    if c2 in board_known:
                        continue
                    result.append([c1, c2])
        elif suited is True:  # Suited only
            for s in range(4):
                c1 = r1 * 4 + s
                c2 = r2 * 4 + s
                if c1 in board_known or c2 in board_known:
                    continue
                result.append([c1, c2])
        elif suited is False:  # Offsuit only
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in board_known:
                    continue
                for s2 in range(4):
                    if s1 == s2:
                        continue
                    c2 = r2 * 4 + s2
                    if c2 in board_known:
                        continue
                    result.append([c1, c2])
        else:  # Both suited and offsuit
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in board_known:
                    continue
                for s2 in range(4):
                    if r1 == r2 and s1 >= s2:
                        continue
                    c2 = r2 * 4 + s2
                    if c2 in board_known:
                        continue
                    result.append([c1, c2])

    return result


def _equity_vs_range(
    hero_hole: list[int],
    board_known: list[int],
    villain_range: list[list[int]],
    evaluator: HandEvaluator,
    deck: DeckConfig,
    simulations: int = 5000,
) -> float:
    """Monte Carlo equity of hero against villain's range of hole cards."""
    known = set(hero_hole + board_known)
    base_deck = [c for c in deck.all_cards() if c not in known]
    remaining_board = 5 - len(board_known)

    if not villain_range:
        return 50.0

    wins = 0
    for _ in range(simulations):
        villain_hole = random.choice(villain_range)

        deck_clean = [c for c in base_deck if c not in villain_hole]
        random.shuffle(deck_clean)

        sim_board = board_known + deck_clean[:remaining_board]

        hero_score = evaluator.best_5(hero_hole + sim_board)
        villain_score = evaluator.best_5(villain_hole + sim_board)

        if hero_score > villain_score:
            wins += 1
        elif hero_score == villain_score:
            wins += 0.5

    return wins / simulations * 100 if simulations > 0 else 50


def _infer_villain_position(hero_position: str, board: list[int]) -> str:
    """Assuming heads-up pot, villain is a typical mid-position player."""
    return "MP"


def calculate_equity(
    hero_cards: list[str],
    board_cards: list[str],
    hero_position: str,
    mode: str = "standard",
    villain_position: str | None = None,
    simulations: int = 5000,
) -> float:
    """Calculate hero's equity against villain range for the given mode.

    Args:
        hero_cards: ['Ah', 'Kh']
        board_cards: ['Ad', 'Tc', '3h']  (0-5 cards)
        hero_position: 'BTN', 'UTG', etc.
        mode: 'standard', 'shortdeck', 'sng', 'squid'
        villain_position: optional override; inferred if None
        simulations: Monte Carlo iterations (default 5000)

    Returns:
        Equity percentage (0-100)
    """
    deck = get_deck_config(mode)
    evaluator = HandEvaluator(deck)

    hero_hole = [deck.parse_card(c) for c in hero_cards]
    board = [deck.parse_card(c) for c in board_cards]
    villain_pos = villain_position or _infer_villain_position(hero_position, board)

    known = set(hero_hole) | set(board)
    villain_range = _generate_range(villain_pos, known, deck)

    if not villain_range:
        return 50.0

    return _equity_vs_range(
        hero_hole, board, villain_range, evaluator, deck, simulations
    )


def calculate_equity_curve(
    hero_cards: list[str],
    board_cards: list[str],
    hero_position: str,
    mode: str = "standard",
    villain_position: str | None = None,
    simulations: int = 3000,
) -> list[dict]:
    """Calculate equity at each street for replay purposes.

    Returns list of {label, equity, pot_size_bb} dicts.
    """
    curve = []
    board_so_far: list[str] = []
    street_labels = ["Preflop", "Flop", "Turn", "River"]
    board_targets = [0, 3, 4, 5]

    known_cards = list(hero_cards)
    for target, label in zip(board_targets, street_labels):
        while len(board_so_far) < target and len(board_so_far) < len(board_cards):
            board_so_far.append(board_cards[len(board_so_far)])
            known_cards.append(board_so_far[-1])

        eq = calculate_equity(
            hero_cards=hero_cards,
            board_cards=board_so_far[:],
            hero_position=hero_position,
            mode=mode,
            villain_position=villain_position,
            simulations=simulations,
        )
        curve.append({"label": label, "equity": eq, "pot_size_bb": 0})
    return curve
