"""Dirty 상태 배지 — 저장되지 않은 변경사항 시각화."""
from __future__ import annotations

from typing import Protocol


class _StreamlitLike(Protocol):
    def markdown(self, body: str, unsafe_allow_html: bool = ...) -> None: ...


_BADGE_HTML = (
    '<div class="ek-dirty-badge">'
    '● Unsaved changes — 변경사항이 저장되지 않았습니다</div>'
)


def render_dirty_badge(is_dirty: bool, container: _StreamlitLike) -> None:
    """is_dirty=True 일 때만 노란 배지 노출."""
    if is_dirty:
        container.markdown(_BADGE_HTML, unsafe_allow_html=True)


def badge_html_for(is_dirty: bool) -> str | None:
    """순수 함수 버전 — 테스트 용도."""
    return _BADGE_HTML if is_dirty else None
