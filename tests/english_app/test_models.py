"""models.py — LLMResult·SessionSchema dataclass 검증."""
from __future__ import annotations

import pytest

from english_app.models import LLMResult, SessionSchema


def test_llm_result_is_frozen():
    r = LLMResult(
        success=True,
        content="hi",
        provider="Ollama",
        model="gemma4:26b",
    )
    with pytest.raises((AttributeError, Exception)):
        r.content = "mutated"  # type: ignore[misc]


def test_session_schema_new_id_format():
    sid = SessionSchema.new_id()
    assert len(sid) == 15  # YYYYMMDD_HHMMSS
    assert sid[8] == "_"
