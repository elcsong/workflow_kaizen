"""Step 5 Quick Capture — JSON 파싱·필드 fallback·transcript 검증."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from english_app.models import ExtractedEntry
from english_app.services.knowledge_extractor import (
    parse_extractor_response,
    to_bank_row,
)


# ---------- parse_extractor_response ----------

def test_parses_clean_json():
    transcript = "neurobiological evidence shows that memory consolidation matters"
    raw = json.dumps(
        {
            "bank": "vocabulary",
            "word_or_pattern": "neurobiological",
            "meaning": "신경생물학적인",
            "quote": "neurobiological evidence shows that memory consolidation",
            "example": "This neurobiological process underlies memory.",
            "note": "형용사로 자주 쓰임",
        }
    )
    entry = parse_extractor_response(raw, transcript=transcript)
    assert entry.bank == "vocabulary"
    assert entry.word_or_pattern == "neurobiological"
    assert entry.meaning == "신경생물학적인"
    assert entry.quote.startswith("neurobiological evidence")


def test_strips_markdown_code_fences():
    raw = "```json\n" + json.dumps(
        {
            "bank": "grammar",
            "word_or_pattern": "not only X but also Y",
            "meaning": "X 뿐 아니라 Y도",
            "quote": "",
            "example": "Not only smart but also kind.",
            "note": "병렬 강조",
        }
    ) + "\n```"
    entry = parse_extractor_response(raw, transcript="")
    assert entry.bank == "grammar"
    assert entry.word_or_pattern.startswith("not only")


def test_falls_back_to_vocabulary_for_invalid_bank():
    raw = json.dumps(
        {
            "bank": "weird-category",
            "word_or_pattern": "x",
            "meaning": "y",
            "quote": "",
            "example": "z",
            "note": "n",
        }
    )
    entry = parse_extractor_response(raw, transcript="")
    assert entry.bank == "vocabulary"  # fallback


def test_handles_missing_fields_with_safe_defaults():
    raw = json.dumps({"bank": "vocabulary", "word_or_pattern": "abc"})
    entry = parse_extractor_response(raw, transcript="")
    assert entry.word_or_pattern == "abc"
    assert entry.meaning == ""
    assert entry.example == ""
    assert entry.note == ""
    assert entry.quote == ""


def test_clears_quote_when_not_in_transcript():
    """LLM 환각 방지 — quote가 transcript에 없으면 빈 문자열로 리셋."""
    raw = json.dumps(
        {
            "bank": "vocabulary",
            "word_or_pattern": "discount",
            "meaning": "할인",
            "quote": "이 문장은 transcript에 존재하지 않는 환각입니다",
            "example": "Get a 10% discount.",
            "note": "",
        }
    )
    entry = parse_extractor_response(
        raw,
        transcript="The speaker mentions discount strategies for retail.",
    )
    assert entry.quote == ""


def test_keeps_quote_when_substring_of_transcript():
    raw = json.dumps(
        {
            "bank": "vocabulary",
            "word_or_pattern": "discount",
            "meaning": "할인",
            "quote": "discount strategies for retail",
            "example": "...",
            "note": "",
        }
    )
    entry = parse_extractor_response(
        raw, transcript="The speaker mentions discount strategies for retail."
    )
    assert "discount strategies" in entry.quote


def test_raises_on_completely_invalid_json():
    with pytest.raises(ValueError):
        parse_extractor_response("this is not json at all", transcript="")


# ---------- to_bank_row ----------

def test_to_bank_row_vocabulary_mapping():
    entry = ExtractedEntry(
        bank="vocabulary",
        word_or_pattern="neurobiological",
        meaning="신경생물학적인",
        quote="...",
        example="A neurobiological example.",
        note="형용사",
    )
    row = to_bank_row(entry)
    assert row == {
        "Word": "neurobiological",
        "Meaning": "신경생물학적인",
        "Example": "A neurobiological example.",
    }


def test_to_bank_row_grammar_mapping():
    entry = ExtractedEntry(
        bank="grammar",
        word_or_pattern="not only X but also Y",
        meaning="병렬 강조",
        quote="",
        example="Not only smart but also kind.",
        note="문어체 강조",
    )
    row = to_bank_row(entry)
    assert row == {
        "Sentence/Pattern": "not only X but also Y",
        "Grammar Point": "병렬 강조",
        "My Note": "문어체 강조",
    }


# ---------- llm_helper.extract_knowledge_entry routing ----------

def test_extract_routes_through_provider_registry():
    from english_app import llm_helper

    fake = MagicMock()

    def fake_stream(_prompt, _model):
        return iter([json.dumps({
            "bank": "vocabulary",
            "word_or_pattern": "test",
            "meaning": "테스트",
            "quote": "",
            "example": "x",
            "note": "",
        })])

    fake.stream.side_effect = fake_stream
    fake.get_last_finish_reason.return_value = "stop"

    with patch.dict(llm_helper._REGISTRY, {"Fake": fake}, clear=False):
        entry = llm_helper.extract_knowledge_entry(
            user_input="test",
            transcript="",
            provider="Fake",
            model_name="m",
        )
    assert entry.word_or_pattern == "test"
    assert entry.bank == "vocabulary"


def test_extract_unknown_provider_returns_failure_marker():
    from english_app import llm_helper

    entry = llm_helper.extract_knowledge_entry(
        user_input="x", transcript="", provider="DoesNotExist", model_name="m"
    )
    assert entry.bank == "vocabulary"
    assert "Error" in entry.meaning or "Error" in entry.note
