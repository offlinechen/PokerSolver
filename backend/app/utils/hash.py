"""SHA256 hash utility for cache keys."""

import hashlib
import json


def compute_hash(*args) -> str:
    """Compute SHA256 hash of the concatenated string representation of args."""
    combined = "|".join(json.dumps(arg, sort_keys=True, default=str) for arg in args)
    return hashlib.sha256(combined.encode()).hexdigest()


def compute_game_state_hash(
    hero_cards: list[str],
    board_cards: list[str],
    position: str,
    stack_size: float,
    pot_size: float,
    actions: list[dict],
    mode: str = "standard",
) -> str:
    """Compute a deterministic hash for a GameState to use as Solver cache key.

    Args:
        mode: Game mode string — ensures different modes don't share caches.
    """
    return compute_hash(
        mode,
        sorted(hero_cards),
        sorted(board_cards),
        position,
        stack_size,
        pot_size,
        actions,
    )
