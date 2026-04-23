"""Ollama Provider — 동적 모델 검출·스트리밍·가용성 검증."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
import requests

from english_app.services.llm.base import ProviderUnavailable
from english_app.services.llm.ollama import OllamaProvider


def _fake_tags_response(names: list[str]) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"models": [{"name": n} for n in names]}
    return resp


class _FakeStreamResponse:
    def __init__(self, lines: list[dict]):
        self._lines = [json.dumps(l) for l in lines]
        self.status_code = 200

    def raise_for_status(self):
        pass

    def iter_lines(self, decode_unicode=True):
        for l in self._lines:
            yield l

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_list_models_dynamic_sorts_default_first():
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _fake_tags_response(
        ["gpt-oss:latest", "gemma4:26b"]
    )
    provider = OllamaProvider(session=session)
    models = provider.list_models()
    assert models[0] == "gemma4:26b"
    assert "gpt-oss:latest" in models


def test_list_models_cached_between_calls():
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _fake_tags_response(["gemma4:26b"])
    provider = OllamaProvider(session=session)
    provider.list_models()
    provider.list_models()
    # 캐시 적중 → 첫 호출만 네트워크 발생
    assert session.get.call_count == 1


def test_list_models_force_refresh_hits_network_again():
    session = MagicMock(spec=requests.Session)
    session.get.return_value = _fake_tags_response(["gemma4:26b"])
    provider = OllamaProvider(session=session)
    provider.list_models()
    provider.list_models(force_refresh=True)
    assert session.get.call_count == 2


def test_list_models_fallback_on_network_error():
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.ConnectionError("server off")
    provider = OllamaProvider(session=session)
    models = provider.list_models()
    assert "gemma4:26b" in models  # fallback 상수에서 제공


def test_is_available_false_when_server_down():
    session = MagicMock(spec=requests.Session)
    session.get.side_effect = requests.ConnectionError("refused")
    provider = OllamaProvider(session=session)
    assert provider.is_available() is False


def test_stream_yields_chunks_and_records_finish_reason():
    session = MagicMock(spec=requests.Session)
    session.post.return_value = _FakeStreamResponse(
        [
            {"message": {"content": "Hello"}, "done": False},
            {"message": {"content": " world"}, "done": False},
            {"done": True, "done_reason": "stop"},
        ]
    )
    provider = OllamaProvider(session=session)
    chunks = list(provider.stream("hi", "gemma4:26b"))
    assert chunks == ["Hello", " world"]
    assert provider.get_last_finish_reason() == "stop"


def test_stream_raises_provider_unavailable_on_network_error():
    session = MagicMock(spec=requests.Session)
    session.post.side_effect = requests.ConnectionError("refused")
    provider = OllamaProvider(session=session)
    with pytest.raises(ProviderUnavailable):
        list(provider.stream("hi", "gemma4:26b"))
