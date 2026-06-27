"""Analyses API — GET analysis detail, list analyses for a hand."""

import json
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.schemas.analysis import AnalysisListResponse, AnalysisResponse
from app.schemas.solver import StrategyBreakdown

if TYPE_CHECKING:
    from app.models.analysis import Analysis

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _format_learning_points(learning_points_str: str | None) -> list[str]:
    """Parse learning_points from JSON string or newline-separated text."""
    if not learning_points_str:
        return []
    try:
        parsed = json.loads(learning_points_str)
        if isinstance(parsed, list):
            return [str(p) for p in parsed]
        return [learning_points_str]
    except (json.JSONDecodeError, TypeError):
        # Assume newline-separated
        return [line.strip() for line in learning_points_str.split("\n") if line.strip()]


def _to_response(analysis: "Analysis") -> AnalysisResponse:
    """Convert an Analysis ORM object to an AnalysisResponse."""
    strategy = StrategyBreakdown(
        call=0,
        raise_=0,
        fold=0,
    )
    if analysis.strategy:
        try:
            strategy_data = json.loads(analysis.strategy)
            strategy = StrategyBreakdown(
                call=float(strategy_data.get("call", 0)),
                raise_=float(strategy_data.get("raise", 0)),
                fold=float(strategy_data.get("fold", 0)),
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    return AnalysisResponse(
        hand_id=analysis.hand_id,
        analysis_id=analysis.id,
        recommendation=analysis.recommendation or "HOLD",
        equity=float(analysis.equity) if analysis.equity else 0,
        call_ev=float(analysis.call_ev) if analysis.call_ev else 0,
        raise_ev=float(analysis.raise_ev) if analysis.raise_ev else 0,
        fold_ev=float(analysis.fold_ev) if analysis.fold_ev else 0,
        strategy=strategy,
        gto_analysis=analysis.gto_analysis or "No GTO analysis available.",
        exploit_analysis=analysis.exploit_analysis or "No exploit analysis available.",
        risk_analysis=analysis.risk_analysis or "No risk analysis available.",
        learning_points=_format_learning_points(analysis.learning_points),
        created_at=analysis.created_at,
    )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    summary="获取单条分析详情",
)
async def get_analysis(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """Get a single analysis by its ID."""
    if settings.fake_mode:
        raise HTTPException(status_code=404, detail="No DB in fake mode")

    from sqlalchemy import select
    from app.models.analysis import Analysis
    query = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(query)
    analysis = result.scalar_one_or_none()

    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return _to_response(analysis)


@router.get(
    "",
    response_model=AnalysisListResponse,
    summary="获取分析列表（可按手牌过滤）",
)
async def list_analyses(
    hand_id: str | None = Query(default=None, description="Filter by hand ID"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    db: AsyncSession = Depends(get_db),
) -> AnalysisListResponse:
    """Get paginated list of analyses, optionally filtered by hand."""
    if settings.fake_mode:
        return AnalysisListResponse(items=[], total=0, page=1, page_size=20)

    from sqlalchemy import func, select
    from app.models.analysis import Analysis
    base_query = select(Analysis)
    count_query = select(func.count(Analysis.id))

    if hand_id:
        base_query = base_query.where(Analysis.hand_id == hand_id)
        count_query = count_query.where(Analysis.hand_id == hand_id)

    # Count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Fetch page
    offset = (page - 1) * page_size
    base_query = base_query.order_by(Analysis.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(base_query)
    analyses = result.scalars().all()

    items = [_to_response(a) for a in analyses]

    return AnalysisListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )
