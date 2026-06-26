"""Poker equity engine — Monte Carlo hand evaluation and equity calculation.

Card encoding: rank (0-12) = 2,3,4,5,6,7,8,9,T,J,Q,K,A
               suit (0-3)  = spades, hearts, diamonds, clubs
               card = rank * 4 + suit
"""

import random
import itertools
from typing import NamedTuple


RANK_MAP: dict[str, int] = {r: i for i, r in enumerate("23456789TJQKA")}
SUIT_MAP: dict[str, int] = {s: i for i, s in enumerate("shdc")}
RANK_NAMES = "23456789TJQKA"


class HandEval(NamedTuple):
    score: int
    ranks: list[int]


def parse_card(card_str: str) -> int:
    """Parse 'Ah' -> card integer."""
    if len(card_str) != 2:
        raise ValueError(f"Invalid card: {card_str}")
    rank = RANK_MAP[card_str[0].upper()]
    suit = SUIT_MAP[card_str[1].lower()]
    return rank * 4 + suit


def encode_rank(card: int) -> int:
    return card // 4


def encode_suit(card: int) -> int:
    return card % 4


def format_card(card: int) -> str:
    rank = RANK_NAMES[encode_rank(card)]
    suit = "shdc"[encode_suit(card)]
    return f"{rank}{suit}"


def all_cards() -> list[int]:
    return list(range(52))


def _score_hand(cards: list[int]) -> int:
    """Score a 5-card hand using prime-bit encoding. Higher = stronger."""
    ranks = sorted((encode_rank(c) for c in cards), reverse=True)
    suits = [encode_suit(c) for c in cards]

    flush = len(set(suits)) == 1
    straight = False
    straight_high = -1
    # Wheels: A-2-3-4-5
    if set(ranks) == {12, 0, 1, 2, 3}:
        straight = True
        straight_high = 3  # 5-high
    elif max(ranks) - min(ranks) == 4 and len(set(ranks)) == 5:
        straight = True
        straight_high = max(ranks)

    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    counts = sorted(rank_counts.values(), reverse=True)
    # Sort ranks by count then by rank
    rank_by_count = sorted(
        rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True
    )

    # Hand category: 8=straight flush, 7=quads, 6=full house, 5=flush, 4=straight,
    # 3=trips, 2=two pair, 1=pair, 0=high card
    if straight and flush:
        category = 8
        tie = [straight_high]
    elif counts == [4, 1]:
        category = 7
        tie = [rank_by_count[0][0], rank_by_count[1][0]]
    elif counts == [3, 2]:
        category = 6
        tie = [rank_by_count[0][0], rank_by_count[1][0]]
    elif flush:
        category = 5
        tie = ranks
    elif straight:
        category = 4
        tie = [straight_high]
    elif counts == [3, 1, 1]:
        category = 3
        kickers = [r for r, c in rank_counts.items() if c == 1]
        tie = [rank_by_count[0][0]] + sorted(kickers, reverse=True)
    elif counts == [2, 2, 1]:
        category = 2
        pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
        kicker = [r for r, c in rank_counts.items() if c == 1][0]
        tie = pairs + [kicker]
    elif counts == [2, 1, 1, 1]:
        category = 1
        pair = [r for r, c in rank_counts.items() if c == 2][0]
        kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
        tie = [pair] + kickers
    else:
        category = 0
        tie = ranks

    # Composite score: category dominates tie-breakers
    # category * 16^5 ensures lower categories never outscore higher ones
    score = category * (16 ** 5)
    for t in tie:
        score = score * 16 + t
    return score


def _best_5(cards: list[int]) -> int:
    """Evaluate best 5-card hand from 5-7 cards."""
    best = -1
    for combo in itertools.combinations(cards, 5):
        s = _score_hand(list(combo))
        if s > best:
            best = s
    return best


def _equity_vs_range(
    hero_hole: list[int],
    board_known: list[int],
    villain_range: list[list[int]],
    simulations: int = 5000,
) -> float:
    """Monte Carlo equity of hero against villain's range of hole cards."""
    known = set(hero_hole + board_known)
    base_deck = [c for c in all_cards() if c not in known]
    remaining_board = 5 - len(board_known)
    random.shuffle(villain_range)

    wins = 0
    total = 0
    for _ in range(simulations):
        # Pick villain hand first
        villain_idx = total % len(villain_range)
        villain_hole = villain_range[villain_idx]
        total += 1

        # Build a clean deck that excludes villain's current hole cards
        deck = [c for c in base_deck if c not in villain_hole]
        random.shuffle(deck)

        # Deal remaining board
        sim_board = board_known + deck[:remaining_board]

        hero_score = _best_5(hero_hole + sim_board)
        villain_score = _best_5(villain_hole + sim_board)

        if hero_score > villain_score:
            wins += 1
        elif hero_score == villain_score:
            wins += 0.5

    return wins / total * 100 if total > 0 else 50


def _generate_villain_range(position: str, board: list[int]) -> list[list[int]]:
    """Generate a representative range of villain hole card pairs.

    Simplified range based on typical GTO opening ranges.
    Returns a list of card pairs (each as [int, int]).

    Note: actual GTO ranges are much more nuanced. This is a simplified
    approximation for Monte Carlo equity calculation.
    """
    ranges: dict[str, list[tuple[int, bool]]] = {
        # (rank_tuple, suited?), suited=True means only suited combos
        "UTG": [
            ((12, 12), None),  # AA
            ((11, 11), None),  # KK
            ((10, 10), None),  # QQ
            ((9, 9), None),  # JJ
            ((8, 8), None),  # TT
            ((7, 7), None),  # 99
            ((12, 11), True),  # AKs
            ((12, 11), False),  # AKo
            ((12, 10), True),  # AQs
            ((12, 9), True),  # AJs
            ((12, 8), True),  # ATs
            ((11, 10), True),  # KQs
            ((11, 9), True),  # KJs
            ((10, 9), True),  # QJs
        ],
        "MP": [
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((11, 10), True),
            ((11, 9), True), ((10, 9), True), ((10, 8), True),
            ((9, 8), True), ((12, 10), False),
        ],
        "HJ": [
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((5, 5), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((12, 7), True),
            ((11, 10), True), ((11, 9), True), ((10, 9), True),
            ((10, 8), True), ((9, 8), True), ((8, 7), True),
            ((12, 10), False), ((11, 10), False),
        ],
        "CO": [
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((5, 5), None), ((4, 4), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((12, 7), True),
            ((12, 6), True), ((12, 5), True),
            ((11, 10), True), ((11, 9), True), ((10, 9), True),
            ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
            ((12, 10), False), ((11, 10), False),
            ((12, 4), True), ((12, 3), True),  # A4s, A3s
        ],
        "BTN": [
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((12, 7), True),
            ((12, 6), True), ((12, 5), True), ((12, 4), True),
            ((12, 3), True), ((12, 2), True),
            ((11, 10), True), ((11, 9), True), ((10, 9), True),
            ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
            ((6, 5), True), ((5, 4), True),
            ((12, 10), False), ((11, 10), False), ((10, 9), False),
            ((12, 9), False), ((11, 9), False),
        ],
        "SB": [
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((12, 7), True),
            ((12, 6), True), ((12, 5), True), ((12, 4), True),
            ((12, 3), True), ((12, 2), True),
            ((11, 10), True), ((11, 9), True), ((10, 9), True),
            ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
            ((6, 5), True), ((5, 4), True),
            ((12, 10), False), ((11, 10), False), ((10, 9), False),
            ((12, 9), False), ((11, 9), False), ((9, 8), False),
        ],
        "BB": [
            # BB defends very wide
            ((12, 12), None), ((11, 11), None), ((10, 10), None),
            ((9, 9), None), ((8, 8), None), ((7, 7), None), ((6, 6), None),
            ((5, 5), None), ((4, 4), None), ((3, 3), None), ((2, 2), None),
            ((12, 11), True), ((12, 11), False), ((12, 10), True),
            ((12, 9), True), ((12, 8), True), ((12, 7), True),
            ((12, 6), True), ((12, 5), True), ((12, 4), True),
            ((12, 3), True), ((12, 2), True),
            ((11, 10), True), ((11, 9), True), ((10, 9), True),
            ((10, 8), True), ((9, 8), True), ((8, 7), True), ((7, 6), True),
            ((6, 5), True), ((5, 4), True),
            ((12, 10), False), ((11, 10), False), ((10, 9), False),
            ((12, 9), False), ((11, 9), False), ((9, 8), False),
            # Extra BB defense
            ((12, 3), False), ((10, 8), False), ((12, 2), False),
        ],
    }

    position = position.upper()
    range_spec = ranges.get(position, ranges["BTN"])  # default to BTN range

    # Build actual hole card pairs (excluding known cards)
    known = set(board)
    # For villain hole cards, we also exclude hero_cards - but that's done
    # at the equity_vs_range level with full known set
    result: list[list[int]] = []

    for (r1, r2), suited in range_spec:
        if r1 == r2:  # Pocket pair
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in known:
                    continue
                for s2 in range(s1 + 1, 4):
                    c2 = r2 * 4 + s2
                    if c2 in known:
                        continue
                    result.append([c1, c2])
        elif suited is True:  # Suited only
            for s in range(4):
                c1 = r1 * 4 + s
                c2 = r2 * 4 + s
                if c1 in known or c2 in known:
                    continue
                result.append([c1, c2])
        elif suited is False:  # Offsuit only
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in known:
                    continue
                for s2 in range(4):
                    if s1 == s2:
                        continue
                    c2 = r2 * 4 + s2
                    if c2 in known:
                        continue
                    result.append([c1, c2])
        else:  # Both suited and offsuit
            for s1 in range(4):
                c1 = r1 * 4 + s1
                if c1 in known:
                    continue
                for s2 in range(4):
                    if r1 == r2 and s1 >= s2:
                        continue  # avoid duplicate pairs
                    c2 = r2 * 4 + s2
                    if c2 in known:
                        continue
                    result.append([c1, c2])

    return result


def calculate_equity(
    hero_cards: list[str],
    board_cards: list[str],
    hero_position: str,
    villain_position: str | None = None,
    simulations: int = 5000,
) -> float:
    """Calculate hero's equity against villain range.

    For preflop, simulates all 5 board cards.
    For postflop, simulates only remaining board cards.
    """
    hero_hole = [parse_card(c) for c in hero_cards]
    board = [parse_card(c) for c in board_cards]
    villain_pos = villain_position or _infer_villain_position(
        hero_position, board
    )

    # Known cards = hero hole + board (villain can't hold these)
    known = set(hero_hole) | set(board)

    villain_range = _generate_villain_range(villain_pos, list(known))
    if not villain_range:
        return 50.0

    return _equity_vs_range(hero_hole, board, villain_range, simulations)


def _infer_villain_position(
    hero_position: str, board: list[int]
) -> str:
    """Assuming heads-up pot, villain is the other position."""
    # Simplified: villain is a typical mid-position player
    # This should ideally be a configuration or derived from action history
    return "MP"
