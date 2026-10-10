"""LLM client initialization and provider management using OpenAI SDK."""

import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Manages connection to OpenAI-compatible LLM endpoints."""

    _client: Optional[OpenAI] = None

    @classmethod
    def get_client(cls) -> Optional[OpenAI]:
        """Returns initialized OpenAI client configured with custom base_url."""
        if not settings.is_llm_configured():
            return None

        if cls._client is None:
            logger.info("Initializing OpenAI client with custom base URL: %s", settings.llm_base_url)
            cls._client = OpenAI(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
            )
        return cls._client

    @classmethod
    def reset_client(cls) -> None:
        """Resets cached client instance (useful for test isolation)."""
        cls._client = None
