"""레거시 shim — Provider 라우팅과 친화적 모델명 매핑 검증."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from english_app import llm_helper


def test_models_dict_exposes_four_providers():
    assert set(llm_helper.MODELS.keys()) == {"Ollama", "OpenAI", "Gemini", "Anthropic"}


def test_friendly_names_for_cloud_providers():
    assert "GPT-5 mini" in llm_helper.MODELS["OpenAI"]
    assert "Claude 4.5 Sonnet" in llm_helper.MODELS["Anthropic"]
    assert "Gemini 2.5 Pro" in llm_helper.MODELS["Gemini"]


def test_stream_routes_to_provider():
    fake_provider = MagicMock()
    fake_provider.stream.return_value = iter(["hi", " there"])
    fake_provider.get_last_finish_reason.return_value = "stop"
    with patch.dict(llm_helper._REGISTRY, {"Fake": fake_provider}, clear=False):
        chunks = list(llm_helper.stream_ai_explanation("text", "Fake", "model-x"))
    assert chunks == ["hi", " there"]
    fake_provider.stream.assert_called_once()


def test_stream_unknown_provider_yields_error():
    chunks = list(llm_helper.stream_ai_explanation("text", "DoesNotExist", "m"))
    assert any("Error" in c for c in chunks)


def test_get_ai_explanation_returns_concatenated_string():
    fake = MagicMock()
    fake.stream.return_value = iter(["A", "B", "C"])
    fake.get_last_finish_reason.return_value = "stop"
    with patch.dict(llm_helper._REGISTRY, {"Fake": fake}, clear=False):
        result = llm_helper.get_ai_explanation("t", "Fake", "m")
    assert result == "ABC"
