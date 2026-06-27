"""Solver factory — returns the configured SolverProvider instance.

Now supports mode-based routing:
- standard / 9max → TexasSolver
- shortdeck      → ShortDeckSolver
- sng            → SNGSolver (M1: standard EV placeholder)
- squid          → SquidSolver (M1: standard EV placeholder)
"""

from app.config import settings
from app.solver.base import SolverProvider
from app.solver.texas_solver import (
    TexasSolver,
    ShortDeckSolver,
    SNGSolver,
    SquidSolver,
)

# Mode → Solver class mapping
MODE_SOLVER_MAP: dict[str, type[SolverProvider]] = {
    "standard": TexasSolver,
    "9max": TexasSolver,
    "6max": TexasSolver,
    "shortdeck": ShortDeckSolver,
    "short": ShortDeckSolver,
    "sng": SNGSolver,
    "squid": SquidSolver,
}


def get_solver(mode: str | None = None) -> SolverProvider:
    """Factory: return SolverProvider based on game mode.

    If mode is not specified, falls back to settings.solver_provider
    (backward compatible with original texas solver config).
    """
    if mode is None:
        # Backward compatible: use config
        provider_name = settings.solver_provider.lower()
        solver_class = MODE_SOLVER_MAP.get(provider_name)
        if solver_class is None:
            raise ValueError(f"Unknown solver provider: {provider_name}")
    else:
        solver_class = MODE_SOLVER_MAP.get(mode.lower())
        if solver_class is None:
            raise ValueError(f"Unknown game mode: {mode}")

    return solver_class()


def get_supported_modes() -> list[str]:
    """Return list of supported game modes."""
    return sorted(set(
        k for k in MODE_SOLVER_MAP
        if k not in ("6max", "short")  # aliases
    ))
