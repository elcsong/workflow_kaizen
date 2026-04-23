"""Anthropic Provider — 스트리밍 + truncation 검증."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from english_app.services.llm.anthropic_provider import (
    DEFAULT_MAX_TOKENS,
    AnthropicProvider,
)


class _FakeStream:
    def __init__(self, chunks: list[str], stop_reason: str = "end_turn"):
        self._chunks = chunks
        self._stop_reason = stop_reason

    @property
    def text_stream(self):
        return iter(self._chunks)

    def get_final_message(self):
        return SimpleNamespace(stop_reason=self._stop_reason)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_is_available_requires_api_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("CLAUDE_API_KEY", raising=False)
    provider = AnthropicProvider()
    assert provider.is_available() is False


def test_stream_yields_chunks_and_records_end_turn():
    client = MagicMock()
    client.messages.stream.return_value = _FakeStream(["Hi", " there"])
    provider = AnthropicProvider(client=client, api_key="a-test")
    chunks = list(provider.stream("hello", "claude-sonnet-4-5"))
    assert chunks == ["Hi", " there"]
    assert provider.get_last_finish_reason() == "end_turn"
    assert provider.was_truncated() is False


def test_stream_flags_truncation_when_stop_reason_is_max_tokens():
    client = MagicMock()
    client.messages.stream.return_value = _FakeStream(
        ["partial"], stop_reason="max_tokens"
    )
    provider = AnthropicProvider(client=client, api_key="a-test")
    list(provider.stream("hello", "claude-sonnet-4-5"))
    assert provider.was_truncated() is True


def test_default_max_tokens_above_previous_1024():
    assert DEFAULT_MAX_TOKENS >= 8192
