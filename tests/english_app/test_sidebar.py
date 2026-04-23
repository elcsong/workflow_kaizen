"""사이드바 컴포넌트 — SidebarSelection dataclass 검증."""
from __future__ import annotations

import pytest

from english_app.ui.components.sidebar import SidebarSelection


def test_selection_is_frozen():
    s = SidebarSelection("Ollama", "gemma4:26b", "gemma4:26b", True)
    with pytest.raises(Exception):
        s.ai_provider = "OpenAI"  # type: ignore[misc]


def test_selection_holds_provider_and_model_id():
    s = SidebarSelection(
        ai_provider="Anthropic",
        ai_model_name="Claude 4.5 Sonnet",
        selected_model_id="claude-sonnet-4-5",
        auto_save_enabled=False,
    )
    assert s.ai_provider == "Anthropic"
    assert s.selected_model_id == "claude-sonnet-4-5"
    assert s.auto_save_enabled is False
