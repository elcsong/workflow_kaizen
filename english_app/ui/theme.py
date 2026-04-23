"""디자인 토큰 CSS 로딩."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_TOKENS_PATH = Path(__file__).resolve().parent.parent / "static" / "tokens.css"


@lru_cache(maxsize=1)
def load_tokens_css() -> str:
    """`static/tokens.css` 내용을 1회만 읽어 캐시."""
    return _TOKENS_PATH.read_text(encoding="utf-8")


def inject_into(streamlit_module) -> None:
    """주어진 streamlit 모듈에 `<style>` 블록으로 토큰을 주입."""
    css = load_tokens_css()
    streamlit_module.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
