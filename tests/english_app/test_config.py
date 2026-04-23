"""config.py — API 키 체크·환경 로딩 검증."""
from __future__ import annotations

import pytest

from english_app.config import (
    API_KEY_ENV_VARS,
    OLLAMA_DEFAULT_MODEL,
    check_cloud_provider_keys,
)


def test_ollama_default_model_is_gemma4():
    assert OLLAMA_DEFAULT_MODEL == "gemma4:26b"


def test_api_key_env_vars_cover_three_cloud_providers():
    assert set(API_KEY_ENV_VARS.keys()) == {"OpenAI", "Gemini", "Anthropic"}


def test_check_cloud_provider_keys_flags_missing(monkeypatch: pytest.MonkeyPatch):
    for env in API_KEY_ENV_VARS.values():
        monkeypatch.delenv(env, raising=False)

    results = check_cloud_provider_keys()
    by_provider = {r.provider: r for r in results}
    for provider in API_KEY_ENV_VARS:
        assert by_provider[provider].available is False
        assert by_provider[provider].reason is not None
