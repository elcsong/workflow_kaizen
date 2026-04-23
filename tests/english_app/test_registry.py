"""Registry — Provider 조립과 가용성 필터."""
from __future__ import annotations

from unittest.mock import MagicMock

from english_app.services.llm.registry import (
    DEFAULT_PROVIDER,
    available_providers,
    build_registry,
)


def test_build_registry_contains_four_providers():
    reg = build_registry()
    assert set(reg.keys()) == {"Ollama", "OpenAI", "Gemini", "Anthropic"}


def test_available_providers_filters_unavailable_and_sorts_default_first():
    ollama = MagicMock()
    ollama.is_available.return_value = True
    openai = MagicMock()
    openai.is_available.return_value = False
    gemini = MagicMock()
    gemini.is_available.return_value = True
    anthropic = MagicMock()
    anthropic.is_available.return_value = True

    registry = {
        "Gemini": gemini,
        "OpenAI": openai,
        "Anthropic": anthropic,
        "Ollama": ollama,
    }
    result = available_providers(registry)

    assert "OpenAI" not in result
    assert result[0] == DEFAULT_PROVIDER
    assert set(result) == {"Ollama", "Gemini", "Anthropic"}
