"""Deck configuration — defines card encoding and valid sets per game mode.

Standard:   52 cards (2-A), ranks: 23456789TJQKA
Short Deck: 36 cards (6-A), ranks: 6789TJQKA  (2-5 removed)
"""

from dataclasses import dataclass

# Card encoding: rank (0-12) = 2,3,4,5,6,7,8,9,T,J,Q,K,A
#                suit (0-3)  = spades, hearts, diamonds, clubs
#                card = rank * 4 + suit

ALL_RANKS_52 = "23456789TJQKA"   # all 13 ranks
ALL_RANKS_36 = "6789TJQKA"        # 6-A only (ranks 4-12)

# Wheel straight sets: {ranks in card encoding (0-12)}
WHEEL_52 = {12, 0, 1, 2, 3}       # A-2-3-4-5 (ranks 12,0,1,2,3)
WHEEL_36 = {12, 4, 5, 6, 7}       # A-6-7-8-9 (ranks 12,4,5,6,7)

# Hand categories (higher = stronger)
# Standard:  SF(8) > Quads(7) > Boat(6) > Flush(5) > Straight(4)
# ShortDeck: SF(8) > Quads(7) > Flush(6) > Boat(5) > Straight(4)  <-- SWAPPED
CATEGORY_NAMES_STANDARD = {
    8: "straight_flush",
    7: "four_of_a_kind",
    6: "full_house",
    5: "flush",
    4: "straight",
    3: "three_of_a_kind",
    2: "two_pair",
    1: "one_pair",
    0: "high_card",
}
CATEGORY_NAMES_SHORTDECK = {
    8: "straight_flush",
    7: "four_of_a_kind",
    6: "flush",          # <-- swapped
    5: "full_house",     # <-- swapped
    4: "straight",
    3: "three_of_a_kind",
    2: "two_pair",
    1: "one_pair",
    0: "high_card",
}

CATEGORY_ORDER = {name: i for i, name in enumerate([
    "high_card", "one_pair", "two_pair", "three_of_a_kind",
    "straight", "flush", "full_house", "four_of_a_kind", "straight_flush"
])}

# Pre-compute: for each mode, which category number maps to which category name,
# and the relative ordering (used to assign the composite score).
CATEGORY_MAP_STANDARD = {k: CATEGORY_ORDER[v] for k, v in CATEGORY_NAMES_STANDARD.items()}
CATEGORY_MAP_SHORTDECK = {k: CATEGORY_ORDER[v] for k, v in CATEGORY_NAMES_SHORTDECK.items()}


@dataclass(frozen=True)
class DeckConfig:
    """Configuration for a specific game-mode deck."""
    mode: str                          # "standard" | "shortdeck"
    total_cards: int                   # 52 or 36
    rank_names: str                    # ordered low-to-high rank characters
    min_rank: int                      # minimum valid rank index (0-12)
    max_rank: int                      # maximum valid rank index (always 12 for Ace)
    wheel_set: set[int]                # ranks that form a wheel straight
    category_map: dict[int, int]       # hand category number → ordering index
    category_names: dict[int, str]     # hand category number → name

    @property
    def valid_ranks(self) -> set[int]:
        return set(range(self.min_rank, self.max_rank + 1))

    def is_valid_rank(self, rank: int) -> bool:
        return self.min_rank <= rank <= self.max_rank

    def is_valid_card(self, card: int) -> bool:
        """Check if the card integer belongs in this deck."""
        rank = card // 4
        return self.is_valid_rank(rank)

    def all_cards(self) -> list[int]:
        """Return all card integers valid for this deck."""
        return [c for c in range(52) if self.is_valid_card(c)]

    @staticmethod
    def parse_card(card_str: str) -> int:
        """Parse 'Ah' -> card integer (works for both deck types)."""
        RANK_MAP: dict[str, int] = {r: i for i, r in enumerate("23456789TJQKA")}
        SUIT_MAP: dict[str, int] = {s: i for i, s in enumerate("shdc")}
        if len(card_str) != 2:
            raise ValueError(f"Invalid card: {card_str}")
        rank = RANK_MAP[card_str[0].upper()]
        suit = SUIT_MAP[card_str[1].lower()]
        return rank * 4 + suit

    @staticmethod
    def encode_rank(card: int) -> int:
        return card // 4

    @staticmethod
    def encode_suit(card: int) -> int:
        return card % 4

    @staticmethod
    def format_card(card: int) -> str:
        RANK_NAMES = "23456789TJQKA"
        SUIT_NAMES = "shdc"
        rank = RANK_NAMES[card // 4]
        suit = SUIT_NAMES[card % 4]
        return f"{rank}{suit}"


def get_deck_config(mode: str) -> DeckConfig:
    """Factory: return DeckConfig for the given game mode."""
    mode = mode.lower()
    if mode in ("standard", "9max", "6max", "texas"):
        return DeckConfig(
            mode="standard",
            total_cards=52,
            rank_names=ALL_RANKS_52,
            min_rank=0,
            max_rank=12,
            wheel_set=WHEEL_52,
            category_map=CATEGORY_MAP_STANDARD,
            category_names=CATEGORY_NAMES_STANDARD,
        )
    elif mode in ("shortdeck", "short", "short_deck"):
        return DeckConfig(
            mode="shortdeck",
            total_cards=36,
            rank_names=ALL_RANKS_36,
            min_rank=4,   # rank 4 = 6
            max_rank=12,  # rank 12 = A
            wheel_set=WHEEL_36,
            category_map=CATEGORY_MAP_SHORTDECK,
            category_names=CATEGORY_NAMES_SHORTDECK,
        )
    else:
        raise ValueError(f"Unknown game mode: {mode}")
