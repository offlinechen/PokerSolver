"""Analyze API — POST /api/v1/analyze"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_analysis_service, get_db
from app.config import settings
from app.schemas.analysis import AnalysisResponse
from app.schemas.game_state import GameStateRequest
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post(
    "",
    response_model=AnalysisResponse,
    summary="分析一手牌",
    description="提交牌局信息，获得 GTO Solver 分析和 AI 教练讲解。",
)
async def analyze_hand(
    request: GameStateRequest,
    db: AsyncSession = Depends(get_db),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    """
    Analyze a poker hand.

    In FAKE_MODE: uses in-memory Solver + AI fallback (no DB/Redis/OpenAI).
    In production: full pipeline with DB persistence and caching.
    """
    if settings.fake_mode:
        from app.services.fake_analysis_service import fake_analysis_service
        return await fake_analysis_service.analyze(request)

    result = await service.analyze(db, request)
    await db.commit()
    return result
