"""Gemini Provider — 스트리밍·가용성 검증."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from english_app.services.llm.gemini_provider import GeminiProvider


def test_is_available_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    provider = GeminiProvider()
    assert provider.is_available() is False

    provider2 = GeminiProvider(api_key="g-test")
    assert provider2.is_available() is True


def test_stream_yields_text_chunks():
    model_mock = MagicMock()
    model_mock.generate_content.return_value = iter(
        [
            SimpleNamespace(text="Bonjour"),
            SimpleNamespace(text=" le monde"),
        ]
    )
    provider = GeminiProvider(
        model_factory=lambda name: model_mock, api_key="g-test"
    )
    chunks = list(provider.stream("hi", "gemini-2.5-flash"))
    assert chunks == ["Bonjour", " le monde"]
    assert provider.get_last_finish_reason() == "stop"


def test_list_models_returns_gemini_25_family():
    provider = GeminiProvider(api_key="g-test")
    assert any("gemini-2.5" in m for m in provider.list_models())
