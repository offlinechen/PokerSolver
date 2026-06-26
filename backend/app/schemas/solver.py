"""Pydantic schemas for Solver results."""

from pydantic import BaseModel, Field


class StrategyBreakdown(BaseModel):
    """GTO strategy frequencies."""
    call: float = Field(default=0, ge=0, le=100)
    raise_: float = Field(default=0, ge=0, le=100, alias="raise")
    fold: float = Field(default=0, ge=0, le=100)

    model_config = {"populate_by_name": True}


class SolverResult(BaseModel):
    """Unified Solver output format."""
    equity: float  # 0-100
    call_ev: float
    raise_ev: float
    fold_ev: float
    strategy: StrategyBreakdown
