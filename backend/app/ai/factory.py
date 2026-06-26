"""AI Coach factory — returns the configured CoachProvider instance."""

from app.ai.base import CoachProvider
from app.ai.openai_provider import OpenAIProvider


def get_coach() -> CoachProvider:
    """Factory: return CoachProvider instance.

    Currently only OpenAI is supported. Future: Claude, Gemini.
    """
    return OpenAIProvider()
