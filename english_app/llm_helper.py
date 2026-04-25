"""레거시 shim — 신규 `services/llm/` Registry를 이전 API 형태로 노출.

Sprint 2에서 app.py를 최소 침습으로 유지하기 위한 호환 레이어.
Sprint 4 모듈 분해 시 app.py가 registry를 직접 import하게 되면 삭제 예정.
"""
from __future__ import annotations

import logging
from typing import Iterator

from english_app.models import ExtractedEntry
from english_app.services.knowledge_extractor import parse_extractor_response
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


def build_summary_critique_prompt(summary: str, transcript: str) -> str:
    """Step 10 요약 첨삭용 프롬프트.

    - 사용자 요약과 원문 transcript를 비교
    - 정확히 포착한 부분 / 놓친 핵심 / 잘못 해석한 부분 / 개선 제안
    - 마지막에 점수와 한 줄 평
    """
    return (
        "You are a Senior English Composition Coach helping a learner who has "
        "just finished a 6-Step TED listening study cycle. Their final task "
        "(Step 10) is to summarize the talk in their own words.\n\n"
        "## Your Goal\n"
        "Compare the learner's summary against the original transcript, then "
        "provide actionable, encouraging feedback (첨삭).\n\n"
        "## Mandatory Output Sections (in this order)\n"
        "### 1. ✅ 정확히 포착한 점 (What they captured well)\n"
        "List 2-3 specific points the learner correctly identified, citing the "
        "matching transcript phrase if useful.\n\n"
        "### 2. ⚠️ 놓친 핵심 (Missed key points)\n"
        "Identify up to 3 important ideas from the transcript that are missing or "
        "underdeveloped in the summary. Quote the relevant transcript line.\n\n"
        "### 3. ✏️ 표현·문법 첨삭 (Expression & grammar corrections)\n"
        "Suggest improvements to specific sentences in the summary. Use this format:\n"
        "- 원문: <user sentence>\n"
        "- 수정: <improved sentence>\n"
        "- 이유: <why>\n\n"
        "### 4. 🎯 점수 & 한 줄 총평 (Score & one-line assessment)\n"
        "Score the summary out of 100 across three axes: 내용 정확도, 핵심 포착, "
        "표현 자연스러움. Conclude with one sentence of encouragement.\n\n"
        "## Style\n"
        "- Respond in **Korean** (Markdown with the section headings above).\n"
        "- Be specific, cite transcript evidence, avoid generic praise.\n"
        "- If the summary is empty or far too short, say so plainly and ask the "
        "learner to write at least 3-5 sentences first.\n\n"
        "## Inputs\n\n"
        "<transcript>\n"
        f"{(transcript or '(자막 없음)')[:6000]}\n"
        "</transcript>\n\n"
        "<learner_summary>\n"
        f"{summary or '(빈 요약)'}\n"
        "</learner_summary>\n"
    )


def stream_ai_summary_critique(
    summary: str,
    transcript: str,
    provider: str,
    model_name: str,
) -> Iterator[str]:
    """Step 10 요약 첨삭 스트리밍."""
    llm = _REGISTRY.get(provider)
    if llm is None:
        yield f"Error: Unknown provider '{provider}'"
        return
    prompt = build_summary_critique_prompt(summary, transcript)
    try:
        yield from llm.stream(prompt, model_name)
    except ProviderUnavailable as exc:
        yield f"Error: {exc}"
    finish = llm.get_last_finish_reason()
    if finish and finish not in {"end_turn", "stop", "stop_sequence"}:
        logger.warning(
            "Provider %s 종료 사유 비정상: %s — 응답이 잘렸을 수 있음",
            provider,
            finish,
        )


def build_extract_prompt(user_input: str, transcript: str) -> str:
    """Step 5 Quick Capture 프롬프트 — JSON 단일 객체 반환을 강제."""
    transcript_window = (transcript or "")[:6000] or "(자막 없음)"
    return (
        "You are a vocabulary/grammar capture assistant for an English learner "
        "studying TED talks. The learner has captured a fragment they didn't "
        "understand. Your job: classify, look it up in the transcript, and "
        "provide a learner-friendly summary.\n\n"
        "Return EXACTLY one JSON object (no markdown fences, no extra prose) "
        "with these fields:\n"
        "{\n"
        "  \"bank\": \"vocabulary\" | \"grammar\",\n"
        "  \"word_or_pattern\": \"<the term as it should appear in the bank>\",\n"
        "  \"meaning\": \"<Korean explanation, concise>\",\n"
        "  \"quote\": \"<exact transcript sentence containing the term, "
        "or empty string if not found>\",\n"
        "  \"example\": \"<one fresh example sentence in English>\",\n"
        "  \"note\": \"<1-2 line learning tip in Korean>\"\n"
        "}\n\n"
        "Rules:\n"
        "- 'vocabulary' = single words or fixed collocations.\n"
        "- 'grammar' = sentence patterns or constructions (e.g., 'not only X "
        "but also Y', 'had I known').\n"
        "- 'quote' MUST be an exact substring from the transcript when found; "
        "otherwise empty string.\n"
        "- Korean for meaning/note. English for example.\n"
        "- Output JSON only.\n\n"
        f"<transcript>\n{transcript_window}\n</transcript>\n\n"
        f"<learner_input>\n{user_input.strip()}\n</learner_input>\n"
    )


def extract_knowledge_entry(
    user_input: str,
    transcript: str,
    provider: str,
    model_name: str,
) -> ExtractedEntry:
    """Step 5 Quick Capture — Provider 호출 + JSON 응답 파싱.

    스트리밍 호출의 청크를 모두 모아 단일 문자열로 만든 뒤
    `parse_extractor_response()` 로 검증·파싱.
    실패 시에도 사용자가 fallback할 수 있도록 의미 있는 ExtractedEntry 반환
    (note에 에러 메시지 노출).
    """
    llm = _REGISTRY.get(provider)
    if llm is None:
        return ExtractedEntry(
            bank="vocabulary",
            word_or_pattern=user_input.strip(),
            meaning="",
            note=f"Error: Unknown provider '{provider}'",
        )

    prompt = build_extract_prompt(user_input, transcript)
    try:
        chunks = list(llm.stream(prompt, model_name))
    except ProviderUnavailable as exc:
        return ExtractedEntry(
            bank="vocabulary",
            word_or_pattern=user_input.strip(),
            meaning="",
            note=f"Error: {exc}",
        )

    raw = "".join(chunks).strip()
    try:
        return parse_extractor_response(raw, transcript)
    except ValueError as exc:
        logger.warning("Extractor 응답 파싱 실패: %s — raw=%r", exc, raw[:200])
        return ExtractedEntry(
            bank="vocabulary",
            word_or_pattern=user_input.strip(),
            meaning="",
            note=f"Error: 응답 파싱 실패 ({exc})",
        )
