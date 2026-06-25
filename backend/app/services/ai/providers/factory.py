from app.core.config import Settings
from app.services.ai.providers.base import LLMProvider
from app.services.ai.providers.groq_provider import GroqProvider
from app.services.exceptions import LLMProviderError


def get_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "groq":
        return GroqProvider(settings)
    raise LLMProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
