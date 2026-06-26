"""Pydantic schemas for analysis request/response."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.solver import SolverResult, StrategyBreakdown


class AnalysisResponse(BaseModel):
    """Response for a hand analysis."""
    hand_id: str
    analysis_id: str
    recommendation: str
    equity: float
    call_ev: float
    raise_ev: float
    fold_ev: float
    strategy: StrategyBreakdown
    gto_analysis: str
    exploit_analysis: str
    risk_analysis: str
    learning_points: list[str] = Field(default_factory=list)
    created_at: datetime


class AnalysisListResponse(BaseModel):
    """Paginated list of analyses."""
    items: list[AnalysisResponse]
    total: int
    page: int
    page_size: int
