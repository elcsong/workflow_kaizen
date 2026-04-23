"""theme 로더 검증."""
from __future__ import annotations

from unittest.mock import MagicMock

from english_app.ui import theme


def test_load_tokens_returns_css_with_tokens():
    css = theme.load_tokens_css()
    assert ":root" in css
    assert "--color-bg" in css
    assert ".ek-dirty-badge" in css


def test_load_tokens_is_cached():
    theme.load_tokens_css.cache_clear()
    a = theme.load_tokens_css()
    b = theme.load_tokens_css()
    assert a is b  # 같은 객체


def test_inject_calls_markdown_with_style_block():
    theme.load_tokens_css.cache_clear()
    streamlit = MagicMock()
    theme.inject_into(streamlit)
    streamlit.markdown.assert_called_once()
    args, kwargs = streamlit.markdown.call_args
    assert args[0].startswith("<style>")
    assert args[0].endswith("</style>")
    assert kwargs["unsafe_allow_html"] is True
