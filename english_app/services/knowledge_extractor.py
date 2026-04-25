"""Step 5 Quick Capture — LLM 응답 파서 + Bank 행 매핑.

LLM 호출과 프롬프트 빌드는 `llm_helper.extract_knowledge_entry()`가 담당.
이 모듈은 **Provider 중립적인 후처리만** 책임진다.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Final

from english_app.models import ExtractedEntry

logger = logging.getLogger(__name__)

VALID_BANKS: Final[frozenset[str]] = frozenset({"vocabulary", "grammar"})
DEFAULT_BANK: Final[str] = "vocabulary"

_CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _strip_code_fences(raw: str) -> str:
    """LLM이 ` ```json … ``` `로 감싸 반환한 경우 안쪽 내용만 추출."""
    match = _CODE_FENCE_RE.match(raw.strip())
    if match:
        return match.group(1).strip()
    return raw.strip()


def parse_extractor_response(raw: str, transcript: str) -> ExtractedEntry:
    """LLM raw 응답 → ExtractedEntry.

    - 코드 펜스 제거
    - JSON 파싱 (실패 시 ValueError)
    - bank 값 검증 (목록 외 값은 vocabulary로 fallback)
    - quote가 transcript에 substring으로 존재하지 않으면 빈 문자열로 리셋 (환각 방지)
    - 누락 필드는 빈 문자열로 채움
    """
    cleaned = _strip_code_fences(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 응답 JSON 파싱 실패: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"JSON 응답이 객체가 아님: {type(data).__name__}")

    bank = str(data.get("bank", "")).strip().lower()
    if bank not in VALID_BANKS:
        logger.info("bank 값 비정상 (%r) → %s로 fallback", bank, DEFAULT_BANK)
        bank = DEFAULT_BANK

    quote = str(data.get("quote", "")).strip()
    if quote and transcript and quote not in transcript:
        logger.info("quote가 transcript에 없음 (환각 가능성) → 빈 문자열로 리셋")
        quote = ""

    return ExtractedEntry(
        bank=bank,
        word_or_pattern=str(data.get("word_or_pattern", "")).strip(),
        meaning=str(data.get("meaning", "")).strip(),
        quote=quote,
        example=str(data.get("example", "")).strip(),
        note=str(data.get("note", "")).strip(),
    )


def to_bank_row(entry: ExtractedEntry) -> dict:
    """ExtractedEntry → 기존 vocab_list / grammar_list 행 형식으로 매핑."""
    if entry.bank == "grammar":
        return {
            "Sentence/Pattern": entry.word_or_pattern,
            "Grammar Point": entry.meaning,
            "My Note": entry.note or entry.example,
        }
    # vocabulary (default)
    return {
        "Word": entry.word_or_pattern,
        "Meaning": entry.meaning,
        "Example": entry.example,
    }
