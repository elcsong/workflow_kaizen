"""Provider 레지스트리 — 런타임에 사용 가능한 Provider만 노출."""
from __future__ import annotations

import logging
from typing import Dict

from english_app.services.llm.anthropic_provider import AnthropicProvider
from english_app.services.llm.base import LLMProvider
from english_app.services.llm.gemini_provider import GeminiProvider
from english_app.services.llm.ollama import OllamaProvider
from english_app.services.llm.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "Ollama"


def build_registry() -> Dict[str, LLMProvider]:
    """4 Provider 인스턴스를 생성해 이름 기준으로 반환."""
    return {
        "Ollama": OllamaProvider(),
        "OpenAI": OpenAIProvider(),
        "Gemini": GeminiProvider(),
        "Anthropic": AnthropicProvider(),
    }


def available_providers(registry: Dict[str, LLMProvider]) -> list[str]:
    """`is_available()` 체크를 통과한 Provider 이름 리스트 (디폴트가 맨 앞)."""
    available: list[str] = []
    for name, provider in registry.items():
        try:
            if provider.is_available():
                available.append(name)
        except Exception as exc:  # pragma: no cover
            logger.warning("Provider %s 가용성 체크 실패: %s", name, exc)
    available.sort(key=lambda n: 0 if n == DEFAULT_PROVIDER else 1)
    return available
