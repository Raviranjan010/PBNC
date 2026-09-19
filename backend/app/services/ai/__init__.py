from backend.app.core.config import settings
from backend.app.services.ai.base import AIProvider, ParsedQuestion, ParsedOption
from backend.app.services.ai.gemini import GeminiProvider
from backend.app.services.ai.openai import OpenAIProvider
from backend.app.services.ai.heuristic import HeuristicProvider

def get_ai_provider() -> AIProvider:
    provider = settings.AI_PROVIDER.lower()
    if provider == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider()
    elif provider == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    return HeuristicProvider()

__all__ = [
    "AIProvider",
    "ParsedQuestion",
    "ParsedOption",
    "GeminiProvider",
    "OpenAIProvider",
    "HeuristicProvider",
    "get_ai_provider",
]
