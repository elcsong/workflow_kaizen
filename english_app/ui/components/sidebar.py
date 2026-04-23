"""학습 모드 사이드바 — Provider 선택, 자동저장, 세션 정보."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping


@dataclass(frozen=True)
class SidebarSelection:
    ai_provider: str
    ai_model_name: str
    selected_model_id: str
    auto_save_enabled: bool


def render_sidebar(
    *,
    st,
    sess: Mapping,
    models: Mapping[str, Mapping[str, str]],
    auto_save_enabled: bool,
    rerun_count: int,
    on_back: Callable[[], None],
    on_delete_request: Callable[[str], None],
) -> SidebarSelection:
    """사이드바를 렌더하고 사용자 선택을 SidebarSelection으로 반환."""
    with st.sidebar:
        st.button(
            "🔙 Back to Dashboard",
            on_click=on_back,
            use_container_width=True,
        )
        st.divider()
        st.caption(f"Session ID: {sess['id']}")
        st.caption(f"Date: {sess['created_at'][:10]}")

        if sess.get("video_title"):
            st.info(f"📺 {sess['video_title']}")

        st.divider()
        st.subheader("🤖 AI Tutor Settings")
        ai_provider = st.selectbox("Select Provider", list(models.keys()))
        model_options = models[ai_provider] if ai_provider else {}
        ai_model_name = st.selectbox("Select Model", list(model_options.keys()))
        selected_model_id = model_options.get(ai_model_name, ai_model_name)

        st.divider()
        new_autosave = st.toggle(
            "💾 자동 저장 (3초)",
            value=auto_save_enabled,
            help="Dirty 상태가 3초 이상 지속되면 자동 저장합니다.",
        )
        st.caption(f"🔁 Reruns this session: {rerun_count}")

        st.divider()
        if st.button(
            "🗑️ Delete Session",
            type="secondary",
            use_container_width=True,
        ):
            on_delete_request(sess["id"])
            st.rerun()

    return SidebarSelection(
        ai_provider=ai_provider,
        ai_model_name=ai_model_name,
        selected_model_id=selected_model_id,
        auto_save_enabled=new_autosave,
    )
