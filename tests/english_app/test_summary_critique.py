"""Step 10 요약 첨삭 — 프롬프트 빌더 + 스트리밍 라우팅."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from english_app import llm_helper


def test_prompt_includes_both_transcript_and_summary():
    prompt = llm_helper.build_summary_critique_prompt(
        summary="My short summary.",
        transcript="The speaker discusses X and Y.",
    )
    assert "My short summary." in prompt
    assert "The speaker discusses X and Y." in prompt
    assert "<learner_summary>" in prompt
    assert "<transcript>" in prompt


def test_prompt_handles_empty_summary_and_transcript():
    prompt = llm_helper.build_summary_critique_prompt(summary="", transcript="")
    # 빈 입력도 안전한 placeholder로 채워져야 함
    assert "(빈 요약)" in prompt
    assert "(자막 없음)" in prompt


def test_prompt_truncates_long_transcript():
    long_transcript = "A" * 10000
    prompt = llm_helper.build_summary_critique_prompt(
        summary="x", transcript=long_transcript
    )
    # 6000자 컷으로 전체가 그대로 들어가지 않아야 함
    assert prompt.count("A") <= 6000


def test_prompt_specifies_required_sections():
    prompt = llm_helper.build_summary_critique_prompt(summary="x", transcript="y")
    for section in [
        "정확히 포착한 점",
        "놓친 핵심",
        "표현·문법 첨삭",
        "점수 & 한 줄 총평",
    ]:
        assert section in prompt


def test_stream_critique_routes_to_provider():
    fake = MagicMock()
    fake.stream.return_value = iter(["chunk-A", "chunk-B"])
    fake.get_last_finish_reason.return_value = "stop"
    with patch.dict(llm_helper._REGISTRY, {"Fake": fake}, clear=False):
        chunks = list(
            llm_helper.stream_ai_summary_critique(
                "summary", "transcript", "Fake", "model-1"
            )
        )
    assert chunks == ["chunk-A", "chunk-B"]
    fake.stream.assert_called_once()


def test_stream_critique_unknown_provider_yields_error():
    chunks = list(
        llm_helper.stream_ai_summary_critique("s", "t", "DoesNotExist", "m")
    )
    assert any("Error" in c for c in chunks)
