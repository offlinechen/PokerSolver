"""Top-level API router — aggregates all v1 route modules."""

from fastapi import APIRouter

from app.api.v1.analyze import router as analyze_router
from app.api.v1.hands import router as hands_router
from app.api.v1.replay import router as replay_router
from app.api.v1.analyses import router as analyses_router

api_router = APIRouter()

api_router.include_router(analyze_router)
api_router.include_router(hands_router)
api_router.include_router(replay_router)
api_router.include_router(analyses_router)
