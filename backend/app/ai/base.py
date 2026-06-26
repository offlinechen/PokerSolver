"""Coach Provider abstract base."""

from abc import ABC, abstractmethod

from app.schemas.game_state import GameStateRequest
from app.schemas.solver import SolverResult


class CoachProvider(ABC):
    """Abstract interface for all AI Coach implementations."""

    @abstractmethod
    async def analyze(
        self,
        game_state: GameStateRequest,
        solver_result: SolverResult,
    ) -> str:
        """Generate natural language analysis based on Solver results."""
        ...

    @abstractmethod
    async def get_provider_name(self) -> str:
        """Return the provider name."""
        ...
