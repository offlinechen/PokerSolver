"""AI Coach factory — returns the configured CoachProvider instance.

Supports: DeepSeek (default), OpenAI (legacy).
"""

from app.config import settings
from app.ai.base import CoachProvider
from app.ai.deepseek_provider import DeepSeekProvider
from app.ai.openai_provider import OpenAIProvider


_provider_map: dict[str, type[CoachProvider]] = {
    "deepseek": DeepSeekProvider,
    "openai": OpenAIProvider,
}


def get_coach() -> CoachProvider:
    """Factory: return CoachProvider based on settings.ai_provider."""
    provider_name = settings.ai_provider.lower()
    provider_class = _provider_map.get(provider_name)
    if provider_class is None:
        raise ValueError(f"Unknown AI provider: {provider_name}. Supported: {list(_provider_map.keys())}")
    return provider_class()
