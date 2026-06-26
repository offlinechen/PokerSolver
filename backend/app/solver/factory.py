"""Solver factory — returns the configured SolverProvider instance."""

from app.config import settings
from app.solver.base import SolverProvider
from app.solver.texas_solver import TexasSolver


def get_solver() -> SolverProvider:
    """Factory: return SolverProvider based on configuration."""
    provider_name = settings.solver_provider.lower()

    providers: dict[str, type[SolverProvider]] = {
        "texas": TexasSolver,
    }

    provider_class = providers.get(provider_name)
    if provider_class is None:
        raise ValueError(f"Unknown solver provider: {provider_name}")

    return provider_class()
