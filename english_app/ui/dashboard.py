"""대시보드 뷰 — 메트릭, 세션 카드 그리드, 학습 히스토리 테이블."""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import pandas as pd

from english_app.services.flashcards import CardStats
from english_app.services.progress import get_progress_stats
from english_app.ui.components.onboarding import (
    ONBOARDING_BODY_MD,
    ONBOARDING_TITLE,
    should_show_onboarding,
)

_STAGE_ICON: dict[str, str] = {
    "Completed": "✅",
    "Phase 3: Output": "🗣️",
    "Phase 2: Analysis": "📝",
    "Phase 1: Listening": "👂",
}


def _enrich_with_stage(sessions: Sequence[Mapping]) -> tuple[list[dict], int, int]:
    """세션 리스트에 icon/stage_label/progress_pct 보강 + 카운트 반환."""
    enriched: list[dict] = []
    completed = 0
    in_progress = 0
    for raw in sessions:
        sess = dict(raw)
        if sess.get("stage_label"):
            stage = sess["stage_label"]
            pct = sess["progress_pct"]
            icon = _STAGE_ICON.get(stage, "📘")
        else:
            stage, pct, icon = get_progress_stats(sess)
            sess["stage_label"] = stage
            sess["progress_pct"] = pct
        sess["icon"] = icon
        if pct == 100:
            completed += 1
        else:
            in_progress += 1
        enriched.append(sess)
    return enriched, completed, in_progress


def render_dashboard(
    *,
    st,
    sessions: Sequence[Mapping],
    onboarding_dismissed: bool,
    on_onboarding_dismiss: Callable[[], None],
    on_create_new: Callable[[], None],
    on_resume: Callable[[str], None],
    on_request_delete: Callable[[str], None],
    card_stats: CardStats | None = None,
    on_start_review: Callable[[], None] | None = None,
    on_rebuild_index: Callable[[], None] | None = None,
) -> None:
    """대시보드 전체 렌더. 콜백으로 외부 의존성을 주입해 테스트 가능."""
    st.title("English Kaizen Dashboard 📊")

    if should_show_onboarding(
        dismissed=onboarding_dismissed,
        session_count=len(sessions),
    ):
        with st.container(border=True):
            st.subheader(ONBOARDING_TITLE)
            st.markdown(ONBOARDING_BODY_MD)
            if st.button("✓ 알겠어요, 시작할게요", type="primary"):
                on_onboarding_dismiss()
                st.rerun()

    enriched, completed, in_progress = _enrich_with_stage(sessions)
    active = [s for s in enriched if s["progress_pct"] != 100]

    # 1) Top metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sessions", len(enriched))
    col2.metric("Completed", completed)
    col3.metric("In Progress", in_progress)
    st.divider()

    # 2) Quick action
    c1, _ = st.columns([1, 3])
    with c1:
        if st.button("➕ Start New Session", type="primary", use_container_width=True):
            on_create_new()
    st.write("")

    # 3) Continue Learning  +  🎴 Today's Review (좌우 동거)
    review_available = card_stats is not None and on_start_review is not None

    if active and review_available:
        # 둘 다 있을 때 — 좌 2/3 (Continue Learning) + 우 1/3 (Today's Review compact)
        left, right = st.columns([2, 1])
        with left:
            _render_continue_learning(st, active, on_resume, on_request_delete)
        with right:
            _render_review_section(
                st=st,
                stats=card_stats,
                on_start_review=on_start_review,
                on_rebuild_index=on_rebuild_index,
                compact=True,
            )
    elif active:
        # Today's Review 미사용 (legacy) — 단독 렌더
        _render_continue_learning(st, active, on_resume, on_request_delete)
    elif review_available:
        # 진행중 세션 없음 — Today's Review가 full-width
        _render_review_section(
            st=st,
            stats=card_stats,
            on_start_review=on_start_review,
            on_rebuild_index=on_rebuild_index,
            compact=False,
        )
        st.info("진행 중인 세션이 없어요. ➕ Start New Session으로 새 학습을 시작하세요.")
    else:
        st.info("No active sessions. Start a new one!")

    st.divider()

    # 4) Learning History
    st.subheader("📜 Learning History")
    if not enriched:
        st.write("No history yet.")
        return

    table_data = []
    for sess in enriched:
        v_title = sess.get("video_title") or sess.get("video_url", "-")
        if len(v_title) > 50:
            v_title = v_title[:50] + "..."
        table_data.append({
            "Date": sess["created_at"][:10],
            "Stage": f"{sess['icon']} {sess['stage_label']}",
            "Video": v_title,
            "ID": sess["id"],
        })
    df = pd.DataFrame(table_data)
    for _, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 3, 4, 2, 1])
        with c1:
            st.write(row["Date"])
        with c2:
            st.write(row["Stage"])
        with c3:
            st.write(row["Video"])
        with c4:
            if st.button("Open", key=f"hist_{row['ID']}"):
                on_resume(row["ID"])
        with c5:
            if st.button("🗑️", key=f"del_hist_{row['ID']}"):
                on_request_delete(row["ID"])
                st.rerun()
        st.divider()


def _render_continue_learning(
    st,
    active: list[dict],
    on_resume: Callable[[str], None],
    on_request_delete: Callable[[str], None],
) -> None:
    """진행 중 세션 카드 그리드. 좌우 분할 시에는 좌측 2/3 컨테이너 안에서 호출됨."""
    st.subheader("🚀 Continue Learning")
    cols = st.columns(3)
    for idx, sess in enumerate(active):
        with cols[idx % 3]:
            with st.container(border=True):
                st.write(f"**{sess['icon']} {sess['stage_label']}**")
                display_title = sess.get("video_title") or sess.get("video_url", "No Video")
                if len(display_title) > 40:
                    display_title = display_title[:40] + "..."
                st.caption(f"📅 {sess['created_at'][:10]}")
                st.text(f"{display_title}")
                st.progress(sess["progress_pct"])
                b1, b2 = st.columns([3, 1])
                with b1:
                    if st.button("Resume", key=f"resume_{sess['id']}", use_container_width=True):
                        on_resume(sess["id"])
                with b2:
                    if st.button("🗑️", key=f"del_card_{sess['id']}", help="Delete Session"):
                        on_request_delete(sess["id"])
                        st.rerun()


def _render_review_section(
    *,
    st,
    stats: CardStats,
    on_start_review: Callable[[], None],
    on_rebuild_index: Callable[[], None] | None,
    compact: bool = False,
) -> None:
    """Today's Review 카드. compact=True 시 좁은 폭(1/3 컬럼)에 맞춰 단순화.

    - compact: 큰 due 숫자 + Start 버튼 + expander로 4 메트릭/Rebuild 숨김
    - full: 4 메트릭 노출 + Start + Rebuild 헤더 우측
    """
    with st.container(border=True):
        if compact:
            st.subheader("🎴 Today's Review")
            if stats.total == 0:
                st.caption(
                    "아직 카드가 없어요. Phase 2 Quick Capture로 캡처하면 "
                    "자동으로 쌓입니다."
                )
            else:
                st.metric("due 오늘", stats.due_today)
                st.caption(f"전체 {stats.total} 카드")
                if stats.due_today == 0:
                    st.success("🎉 오늘 분량 완료!")
                else:
                    if st.button(
                        f"▶ Start ({stats.due_today})",
                        type="primary",
                        key="dash_start_review",
                        use_container_width=True,
                    ):
                        on_start_review()
                        st.rerun()
                with st.expander("자세히", expanded=False):
                    sub_cols = st.columns(3)
                    sub_cols[0].metric("신규", stats.new)
                    sub_cols[1].metric("학습 중", stats.learning)
                    sub_cols[2].metric("마스터", stats.mature)
                    if on_rebuild_index is not None:
                        if st.button(
                            "🔄 인덱스 재빌드",
                            help="세션 변경 반영",
                            use_container_width=True,
                            key="dash_rebuild_idx",
                        ):
                            on_rebuild_index()
                            st.toast("인덱스를 재빌드했습니다.", icon="🔄")
                            st.rerun()
            return

        # full 모드 (Continue Learning이 비어있을 때)
        head_cols = st.columns([3, 1])
        with head_cols[0]:
            st.subheader("🎴 Today's Review")
        with head_cols[1]:
            if on_rebuild_index is not None:
                if st.button(
                    "🔄 Rebuild",
                    help="카드 인덱스 재빌드 (세션 변경 반영)",
                    use_container_width=True,
                    key="dash_rebuild_idx",
                ):
                    on_rebuild_index()
                    st.toast("인덱스를 재빌드했습니다.", icon="🔄")
                    st.rerun()

        m_cols = st.columns(4)
        m_cols[0].metric("due 오늘", stats.due_today)
        m_cols[1].metric("신규", stats.new)
        m_cols[2].metric("학습 중", stats.learning)
        m_cols[3].metric("마스터", stats.mature)

        if stats.total == 0:
            st.info(
                "아직 카드가 없어요. Phase 2 Quick Capture로 단어를 캡처하면 "
                "자동으로 Bank에 쌓입니다."
            )
        elif stats.due_today == 0:
            st.success("오늘 복습할 카드가 없어요. 잘 하고 있어요! 🎉")
        else:
            if st.button(
                f"▶ Start Review ({stats.due_today}장)",
                type="primary",
                key="dash_start_review",
            ):
                on_start_review()
                st.rerun()
