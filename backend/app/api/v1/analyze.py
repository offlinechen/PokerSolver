"""Analyze API — POST /api/v1/analyze + GET /api/v1/modes"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_analysis_service, get_db
from app.config import settings
from app.schemas.analysis import AnalysisResponse
from app.schemas.game_state import GameStateRequest
from app.services.analysis_service import AnalysisService

router = APIRouter(tags=["analyze"])


@router.get("/modes", summary="获取支持的游戏模式列表")
async def list_modes():
    """Return supported game modes."""
    from app.solver.factory import get_supported_modes
    return {
        "modes": [
            {"id": "standard", "name": "标准德州", "description": "52张牌标准德州扑克"},
            {"id": "shortdeck", "name": "短牌模式", "description": "36张牌(6-A)，同花>葫芦"},
            {"id": "sng", "name": "SNG模式", "description": "坐满即开锦标赛 (ICM将于M2加入)"},
            {"id": "squid", "name": "鱿鱼模式", "description": "生存淘汰赛制 (将于M2加入)"},
        ]
    }


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="分析一手牌",
    description="提交牌局信息，获得 GTO Solver 分析和 AI 教练讲解。支持多种游戏模式。",
)
async def analyze_hand(
    request: GameStateRequest,
    db: AsyncSession = Depends(get_db),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisResponse:
    """
    Analyze a poker hand.

    M1: mode + hero_cards + board_cards + position + stack/pot → EV + recommendation
    M2: + action_history analysis + opponent profiles

    In FAKE_MODE: uses in-memory Solver + AI fallback (no DB/Redis/OpenAI).
    In production: full pipeline with DB persistence and caching.
    """
    if settings.fake_mode:
        from app.services.fake_analysis_service import fake_analysis_service
        return await fake_analysis_service.analyze(request)

    result = await service.analyze(db, request)
    await db.commit()
    return result
