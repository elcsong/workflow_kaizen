"""Player HTML 빌더 검증."""
from __future__ import annotations

from unittest.mock import MagicMock

from english_app.ui.components.player import build_player_html, render_custom_player


def test_build_includes_video_id():
    html = build_player_html("dQw4w9WgXcQ")
    assert "dQw4w9WgXcQ" in html
    assert "iframe_api" in html
    assert "🔁 Loop" in html


def test_render_calls_components_html_with_height():
    components = MagicMock()
    render_custom_player("abc", components)
    components.html.assert_called_once()
    args, kwargs = components.html.call_args
    assert kwargs.get("height") == 420
    assert "abc" in args[0]
