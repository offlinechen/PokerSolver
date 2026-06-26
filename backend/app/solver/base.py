"""Solver Provider abstract base."""

from abc import ABC, abstractmethod

from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult


class SolverProvider(ABC):
    """Abstract interface for all Solver implementations."""

    @abstractmethod
    async def solve(self, game_state: GameStateRequest) -> SolverResult:
        """Compute GTO analysis for the given game state."""
        ...

    @abstractmethod
    async def get_provider_name(self) -> str:
        """Return the provider name."""
        ...
