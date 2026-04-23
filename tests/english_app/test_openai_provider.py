"""OpenAI Provider — 스트리밍·가용성 검증."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from english_app.services.llm.openai_provider import OpenAIProvider


def _make_chunk(text: str | None, finish: str | None = None):
    delta = SimpleNamespace(content=text)
    choice = SimpleNamespace(delta=delta, finish_reason=finish)
    return SimpleNamespace(choices=[choice])


def test_is_available_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider()
    assert provider.is_available() is False

    provider2 = OpenAIProvider(api_key="sk-test")
    assert provider2.is_available() is True


def test_stream_yields_content_and_records_finish_reason():
    client = MagicMock()
    client.chat.completions.create.return_value = iter(
        [
            _make_chunk("Hello"),
            _make_chunk(" world"),
            _make_chunk(None, finish="stop"),
        ]
    )
    provider = OpenAIProvider(client=client, api_key="sk-test")
    result = list(provider.stream("hi", "gpt-5-mini-2025-08-07"))
    assert result == ["Hello", " world"]
    assert provider.get_last_finish_reason() == "stop"


def test_list_models_returns_gpt5_family():
    provider = OpenAIProvider(api_key="sk-test")
    models = provider.list_models()
    assert any("gpt-5" in m for m in models)
