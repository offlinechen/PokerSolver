"""Cache service — Solver and AI result caching with Redis + DB."""

import json
from datetime import datetime, timezone
from uuid import uuid4

import redis.asyncio as aioredis
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas.solver import SolverResult


class CacheService:
    """Handles caching for Solver results and AI analysis results."""

    SOLVER_CACHE_PREFIX = "solver:"
    AI_CACHE_PREFIX = "ai:"
    SOLVER_TTL = 86400  # 24 hours
    AI_TTL = 604800  # 7 days

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    # --- Solver Cache ---

    async def get_solver_result(self, state_hash: str) -> SolverResult | None:
        """Get cached Solver result from Redis."""
        redis = await self._get_redis()
        cached = await redis.get(f"{self.SOLVER_CACHE_PREFIX}{state_hash}")
        if cached:
            data = json.loads(cached)
            return SolverResult(**data)
        return None

    async def set_solver_result(self, state_hash: str, result: SolverResult) -> None:
        """Cache Solver result in Redis."""
        redis = await self._get_redis()
        data = result.model_dump()
        await redis.setex(
            f"{self.SOLVER_CACHE_PREFIX}{state_hash}",
            self.SOLVER_TTL,
            json.dumps(data),
        )

    # --- AI Cache ---

    async def get_ai_result(self, prompt_hash: str) -> str | None:
        """Get cached AI analysis from Redis."""
        redis = await self._get_redis()
        return await redis.get(f"{self.AI_CACHE_PREFIX}{prompt_hash}")

    async def set_ai_result(self, prompt_hash: str, analysis: str) -> None:
        """Cache AI analysis in Redis."""
        redis = await self._get_redis()
        await redis.setex(
            f"{self.AI_CACHE_PREFIX}{prompt_hash}",
            self.AI_TTL,
            analysis,
        )

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Singleton
cache_service = CacheService()
