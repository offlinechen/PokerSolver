"""Hand evaluator — scores a 5-7 card hand using mode-specific rules.

Standard:  Flush(5) > Straight(4), Wheel = A-2-3-4-5, Full House(6) > Flush(5)
ShortDeck: Flush(6) > Full House(5), Wheel = A-6-7-8-9
"""

import itertools

from app.solver.engine.deck import DeckConfig, get_deck_config


class HandEvaluator:
    """Evaluates the best 5-card hand from a set of cards for a specific mode."""

    def __init__(self, deck: DeckConfig):
        self.deck = deck

    def score_hand(self, cards: list[int]) -> int:
        """Score a **5-card** hand. Higher = stronger.

        Composite score encoding:
          score = category_order * 16^5  +  tie[0]*16^4 + tie[1]*16^3 + ...
        This ensures a lower category can never outscore a higher one.
        """
        ranks = sorted([self.deck.encode_rank(c) for c in cards], reverse=True)
        suits = [self.deck.encode_suit(c) for c in cards]

        flush = len(set(suits)) == 1

        # --- Straight detection (mode-dependent wheel) ---
        straight = False
        straight_high = -1
        rank_set = set(ranks)
        if rank_set == self.deck.wheel_set:
            straight = True
            straight_high = max(self.deck.wheel_set - {12})  # highest non-Ace
        elif max(ranks) - min(ranks) == 4 and len(rank_set) == 5:
            straight = True
            straight_high = max(ranks)

        # --- Rank counts ---
        rank_counts: dict[int, int] = {}
        for r in ranks:
            rank_counts[r] = rank_counts.get(r, 0) + 1
        counts = sorted(rank_counts.values(), reverse=True)
        rank_by_count = sorted(
            rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True
        )

        # --- Determine raw category ---
        if straight and flush:
            raw_cat = 8  # straight flush
            tie = [straight_high]
        elif counts == [4, 1]:
            raw_cat = 7  # four of a kind
            tie = [rank_by_count[0][0], rank_by_count[1][0]]
        elif counts == [3, 2]:
            raw_cat = 6  # full house (standard) or flush (short deck)
            tie = [rank_by_count[0][0], rank_by_count[1][0]]
        elif flush:
            raw_cat = 5  # flush (standard) or full house (short deck)
            tie = ranks
        elif straight:
            raw_cat = 4  # straight
            tie = [straight_high]
        elif counts == [3, 1, 1]:
            raw_cat = 3  # three of a kind
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            tie = [rank_by_count[0][0]] + kickers
        elif counts == [2, 2, 1]:
            raw_cat = 2  # two pair
            pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)
            kicker = [r for r, c in rank_counts.items() if c == 1][0]
            tie = pairs + [kicker]
        elif counts == [2, 1, 1, 1]:
            raw_cat = 1  # one pair
            pair = [r for r, c in rank_counts.items() if c == 2][0]
            kickers = sorted([r for r, c in rank_counts.items() if c == 1], reverse=True)
            tie = [pair] + kickers
        else:
            raw_cat = 0  # high card
            tie = ranks

        # --- Map raw category to mode-specific ordering ---
        cat_order = self.deck.category_map[raw_cat]

        # Composite score
        score = cat_order * (16 ** 5)
        for t in tie:
            score = score * 16 + t
        return score

    def best_5(self, cards: list[int]) -> int:
        """Evaluate best 5-card hand from 5-7 cards."""
        best = -1
        for combo in itertools.combinations(cards, 5):
            s = self.score_hand(list(combo))
            if s > best:
                best = s
        return best


def evaluate_hand(cards: list[int], mode: str = "standard") -> int:
    """Convenience: score a 5-card hand."""
    deck = get_deck_config(mode)
    evaluator = HandEvaluator(deck)
    return evaluator.score_hand(cards)


def best_5_cards(cards: list[int], mode: str = "standard") -> int:
    """Convenience: best 5-card score from 5-7 cards."""
    deck = get_deck_config(mode)
    evaluator = HandEvaluator(deck)
    return evaluator.best_5(cards)
