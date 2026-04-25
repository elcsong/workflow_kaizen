"""Flash Card 리뷰 페이지 — 카드 한 장씩 진행, 평가, 종료 요약."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

from english_app.services.flashcards import (
    Card,
    select_today_queue,
    sm2_schedule,
    upsert_card,
)
from english_app.ui.components.flashcard import (
    render_card_back,
    render_card_front,
    render_rating_buttons,
)

# 세션 상태 키
_QUEUE_KEY = "review_queue"          # 남은 카드 리스트
_FLIPPED_KEY = "review_flipped"      # 현재 카드 뒷면 노출 여부
_SUMMARY_KEY = "review_summary"      # 평가 분포 누적 (4-tuple)


def init_review_session(st, candidates: list[Card]) -> None:
    """리뷰 시작 시 세션 상태 초기화."""
    queue = select_today_queue(candidates)
    st.session_state[_QUEUE_KEY] = queue
    st.session_state[_FLIPPED_KEY] = False
    st.session_state[_SUMMARY_KEY] = [0, 0, 0, 0]  # rating 0..3 카운트


def render_review(
    *,
    st,
    review_dir: Path,
    today: date,
    on_back_to_dashboard: Callable[[], None],
) -> None:
    """리뷰 페이지 메인 — 큐 소진까지 카드 한 장씩 표출."""
    queue: list[Card] = st.session_state.get(_QUEUE_KEY, [])

    # 진행률 + 종료 버튼
    total = (
        len(queue) + sum(st.session_state.get(_SUMMARY_KEY, [0, 0, 0, 0]))
    )
    done = sum(st.session_state.get(_SUMMARY_KEY, [0, 0, 0, 0]))

    header_cols = st.columns([6, 1])
    with header_cols[0]:
        if total > 0:
            st.progress(done / total, text=f"Progress: {done} / {total}")
        else:
            st.info("오늘 복습할 카드가 없습니다.")
    with header_cols[1]:
        if st.button("🏠 종료", use_container_width=True):
            on_back_to_dashboard()
            return

    # 큐가 비었으면 요약 화면
    if not queue:
        _render_summary(st, on_back_to_dashboard)
        return

    current = queue[0]
    flipped = st.session_state.get(_FLIPPED_KEY, False)

    with st.container(border=True):
        render_card_front(current, st)

        if not flipped:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            if st.button(
                "🔄 답 보기",
                key=f"flip_{current.id}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state[_FLIPPED_KEY] = True
                st.rerun()
            st.caption("스페이스바로도 카드를 뒤집을 수 있도록 향후 지원 예정.")
        else:
            st.divider()
            render_card_back(current, st)
            st.write("")
            render_rating_buttons(
                current,
                st,
                on_rate=lambda c, r: _handle_rating(st, c, r, review_dir, today),
            )


def _handle_rating(
    st, card: Card, rating: int, review_dir: Path, today: date
) -> None:
    """평가 적용 — SM-2 일정 갱신 + 인덱스 저장 + 큐 진행."""
    updated = sm2_schedule(card, rating=rating, today=today)
    upsert_card(review_dir, updated)

    queue = list(st.session_state.get(_QUEUE_KEY, []))
    if queue and queue[0].id == card.id:
        queue.pop(0)
    st.session_state[_QUEUE_KEY] = queue
    st.session_state[_FLIPPED_KEY] = False

    summary = list(st.session_state.get(_SUMMARY_KEY, [0, 0, 0, 0]))
    summary[rating] += 1
    st.session_state[_SUMMARY_KEY] = summary

    st.rerun()


def _render_summary(st, on_back_to_dashboard: Callable[[], None]) -> None:
    """모든 카드 종료 후 분포 요약."""
    summary = st.session_state.get(_SUMMARY_KEY, [0, 0, 0, 0])
    total = sum(summary)

    with st.container(border=True):
        st.success(f"✅ {total} 카드 복습 완료!")
        if total > 0:
            st.markdown(
                f"**분포**: ❌ 모름 **{summary[0]}** · "
                f"😬 어려움 **{summary[1]}** · "
                f"🙂 좋음 **{summary[2]}** · "
                f"😎 쉬움 **{summary[3]}**"
            )
        if st.button("🏠 Dashboard로 돌아가기", type="primary"):
            # 상태 정리
            for key in (_QUEUE_KEY, _FLIPPED_KEY, _SUMMARY_KEY):
                st.session_state.pop(key, None)
            on_back_to_dashboard()
