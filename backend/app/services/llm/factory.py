from app.services.llm.base import LLMProvider
from app.services.llm.claude_provider import ClaudeProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.core.config import settings


def get_llm_provider(
    ai_provider: str | None = None,
    api_key: str | None = None,
) -> LLMProvider:
    """
    Kullanıcının seçtiği provider'a göre LLM istemcisi döndürür.
    ai_provider: "claude" | "openai" — None ise settings'teki default kullanılır.
    api_key: Seller'a özel API key (None ise .env'den alınır).
    """
    provider = (ai_provider or settings.DEFAULT_AI_PROVIDER).lower()
    if provider == "openai":
        return OpenAIProvider(api_key=api_key)
    return ClaudeProvider(api_key=api_key)
