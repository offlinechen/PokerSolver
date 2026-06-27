"""Solver engine modules — pluggable deck and hand evaluation per game mode."""

from app.solver.engine.deck import DeckConfig, get_deck_config
from app.solver.engine.hand_evaluator import HandEvaluator, evaluate_hand, best_5_cards

__all__ = [
    "DeckConfig",
    "get_deck_config",
    "HandEvaluator",
    "evaluate_hand",
    "best_5_cards",
]
