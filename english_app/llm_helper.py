"""레거시 shim — 신규 `services/llm/` Registry를 이전 API 형태로 노출.

Sprint 2에서 app.py를 최소 침습으로 유지하기 위한 호환 레이어.
Sprint 4 모듈 분해 시 app.py가 registry를 직접 import하게 되면 삭제 예정.
"""
from __future__ import annotations

import logging
from typing import Iterator

from english_app.services.llm.base import ProviderUnavailable
from english_app.services.llm.registry import build_registry

logger = logging.getLogger(__name__)

_REGISTRY = build_registry()


# 친화적 표시명 유지 (레거시 호환). Ollama는 동적 검출이라 ID 그대로.
_FRIENDLY_NAMES: dict[str, dict[str, str]] = {
    "OpenAI": {
        "GPT-5 mini": "gpt-5-mini-2025-08-07",
        "GPT-5.1": "gpt-5.1-2025-11-13",
    },
    "Gemini": {
        "Gemini 2.5 Pro": "gemini-2.5-pro",
        "Gemini 2.5 Flash": "gemini-2.5-flash",
    },
    "Anthropic": {
        "Claude 4.5 Sonnet": "claude-sonnet-4-5",
        "Claude 4.5 Haiku": "claude-haiku-4-5",
    },
}


def _models_for(provider_name: str) -> dict[str, str]:
    """UI에 노출할 '모델 표시명 → API 모델 ID' 매핑."""
    if provider_name in _FRIENDLY_NAMES:
        return dict(_FRIENDLY_NAMES[provider_name])
    provider = _REGISTRY.get(provider_name)
    if provider is None:
        return {}
    # Ollama: ID를 표시명으로 (gemma4:26b 등)
    return {m: m for m in provider.list_models()}


# ---- 레거시 API 유지 ----

MODELS: dict[str, dict[str, str]] = {
    "Ollama": _models_for("Ollama"),
    "OpenAI": _models_for("OpenAI"),
    "Gemini": _models_for("Gemini"),
    "Anthropic": _models_for("Anthropic"),
}


def stream_ai_explanation(
    text: str,
    provider: str,
    model_name: str,
    context: str | None = None,
) -> Iterator[str]:
    """신규 스트리밍 API — `st.write_stream()`에 직접 넘겨 사용."""
    llm = _REGISTRY.get(provider)
    if llm is None:
        yield f"Error: Unknown provider '{provider}'"
        return
    prompt = _build_prompt(text)
    try:
        yield from llm.stream(prompt, model_name, context=context)
    except ProviderUnavailable as exc:
        yield f"Error: {exc}"
    finish = llm.get_last_finish_reason()
    if finish and finish not in {"end_turn", "stop", "stop_sequence"}:
        logger.warning(
            "Provider %s 종료 사유 비정상: %s — 응답이 잘렸을 수 있음",
            provider,
            finish,
        )


def get_ai_explanation(
    text: str,
    provider: str,
    model_name: str,
    context: str | None = None,
) -> str:
    """레거시 동기 API — 스트림을 수집해 문자열로 반환 (기존 호출부 호환용)."""
    chunks = list(stream_ai_explanation(text, provider, model_name, context))
    return "".join(chunks)


def _build_prompt(text: str) -> str:
    """기존 llm_helper의 system prompt를 Provider 중립 형태로 유지."""
    return (
        "You are a Senior Linguistic Analysis Agent specialized in deep grammar "
        "deconstruction of English sentences (typically from TED transcripts).\n\n"
        "## Goal\n"
        "Analyze the user-provided sentence by breaking down its syntax, defining "
        "the grammatical function of every part, and providing practical "
        "composition guidance.\n\n"
        "## Steps (mandatory, in order)\n"
        "1. Structural Breakdown — identify main clause; deconstruct modifiers; "
        "present a visual syntax map.\n"
        "2. Functional Deep Dive — ask one focused grammar inquiry; explain why "
        "the speaker chose this structure.\n"
        "3. Composition Bridging — extract the core pattern; provide 3 original "
        "parallel sentences.\n"
        "4. Self-Reflection & Next Step — review your analysis; conclude with a "
        "prompt for the user's response or next sentence.\n\n"
        "Respond in Korean. Use Markdown with headings, bolding, and lists.\n\n"
        f"Text to analyze:\n{text}"
    )
