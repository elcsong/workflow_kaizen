"""대시보드 뷰 — 메트릭, 세션 카드 그리드, 학습 히스토리 테이블."""
from __future__ import annotations

from typing import Callable, Mapping, Sequence

import pandas as pd

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

    # 3) Continue Learning (cards)
    if active:
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
