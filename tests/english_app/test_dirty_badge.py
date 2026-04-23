"""Dirty 배지 노출 로직."""
from __future__ import annotations

from unittest.mock import MagicMock

from english_app.ui.components.dirty_badge import (
    badge_html_for,
    render_dirty_badge,
)


def test_badge_html_only_when_dirty():
    assert badge_html_for(True) is not None
    assert "Unsaved" in badge_html_for(True)
    assert badge_html_for(False) is None


def test_render_dirty_badge_calls_markdown_only_when_dirty():
    container = MagicMock()
    render_dirty_badge(False, container)
    container.markdown.assert_not_called()

    render_dirty_badge(True, container)
    container.markdown.assert_called_once()
