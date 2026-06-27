"""Solver package."""

from app.solver.base import SolverProvider
from app.solver.factory import get_solver, get_supported_modes
from app.solver.texas_solver import TexasSolver, ShortDeckSolver, SNGSolver, SquidSolver

__all__ = [
    "SolverProvider",
    "get_solver",
    "get_supported_modes",
    "TexasSolver",
    "ShortDeckSolver",
    "SNGSolver",
    "SquidSolver",
]
