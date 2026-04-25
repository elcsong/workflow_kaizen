"""Flash Card 시각 컴포넌트 — 앞면/뒷면/평가 버튼.

Streamlit 호출은 의존성 주입(`st`)을 통해 단위 테스트 가능하도록 분리.
"""
from __future__ import annotations

from typing import Callable

from english_app.services.flashcards import Card

QUOTE_PREVIEW_CHARS = 200


def render_card_front(card: Card, st) -> None:
    """앞면 — 큰 단어/패턴 + 출처 강의."""
    if card.session_title:
        st.caption(f"📺 {card.session_title}")
    st.markdown(
        f"<div class='ek-flashcard-front'>{_html_escape(card.front)}</div>",
        unsafe_allow_html=True,
    )


def render_card_back(card: Card, st) -> None:
    """뒷면 — 뜻, 예시, 본문 인용 토글."""
    if card.meaning:
        st.markdown(f"**📖 뜻**: {card.meaning}")
    if card.example:
        st.markdown(f"💡 **예시**: _{card.example}_")
    if card.quote:
        preview = card.quote[:QUOTE_PREVIEW_CHARS]
        truncated = len(card.quote) > QUOTE_PREVIEW_CHARS
        with st.expander("📍 본문 보기", expanded=False):
            st.info(preview + ("..." if truncated else ""))
            if truncated:
                if st.button("전체 보기", key=f"quote_full_{card.id}"):
                    st.text_area(
                        "Full quote",
                        value=card.quote,
                        height=200,
                        disabled=True,
                        key=f"quote_full_text_{card.id}",
                        label_visibility="collapsed",
                    )


def render_rating_buttons(
    card: Card,
    st,
    *,
    on_rate: Callable[[Card, int], None],
) -> None:
    """4-단계 자가평가 버튼.

    rating: 0=모름, 1=어려움, 2=좋음, 3=쉬움
    """
    cols = st.columns(4)
    labels = [
        ("❌ 모름", 0, "secondary"),
        ("😬 어려움", 1, "secondary"),
        ("🙂 좋음", 2, "secondary"),
        ("😎 쉬움", 3, "primary"),
    ]
    for col, (label, rating, btn_type) in zip(cols, labels):
        with col:
            if st.button(
                label,
                key=f"rate_{card.id}_{rating}",
                use_container_width=True,
                type=btn_type,
            ):
                on_rate(card, rating)
    st.caption("키보드 단축키: 1 모름 · 2 어려움 · 3 좋음 · 4 쉬움")


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
