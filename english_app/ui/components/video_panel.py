"""학습 모드 좌측 비디오 패널 — URL 입력, 저장/새로고침, 플레이어, 외부 열기."""
from __future__ import annotations

from typing import Any, Callable, MutableMapping


def render_video_panel(
    *,
    st,
    sess: MutableMapping,
    cached_video_info: Callable[[str], tuple[str, str, str | None]],
    on_save: Callable[[], None],
    on_dirty: Callable[[], None],
    render_player: Callable[[str], None],
) -> None:
    """좌측 비디오 패널 렌더 — URL 변경 감지·캐시·플레이어."""
    video_url = st.text_input(
        "Video URL",
        value=sess.get("video_url", ""),
        placeholder="Paste YouTube link here...",
    )
    if video_url and video_url != sess.get("video_url", ""):
        sess["video_url"] = video_url
        with st.spinner("Fetching video info & transcript..."):
            title, transcript, v_id = cached_video_info(video_url)
            sess["video_title"] = title
            sess["video_transcript"] = transcript
            sess["video_id"] = v_id
        on_dirty()
        st.rerun()

    col_save, col_refresh = st.columns([3, 1])
    with col_save:
        if st.button("💾 Save Progress", type="primary", use_container_width=True):
            on_save()
    with col_refresh:
        if st.button(
            "🔄",
            help="비디오 메타데이터 다시 가져오기 (제목·자막)",
            use_container_width=True,
        ):
            _clear = getattr(cached_video_info, "clear", None)
            if callable(_clear):
                _clear()
            if video_url:
                with st.spinner("Re-fetching video info..."):
                    title, transcript, v_id = cached_video_info(video_url)
                    sess["video_title"] = title
                    sess["video_transcript"] = transcript
                    sess["video_id"] = v_id
                on_dirty()
                st.toast(
                    "메타데이터 갱신 완료. 저장 버튼을 눌러 반영하세요.",
                    icon="🔄",
                )
                st.rerun()

    st.divider()

    if not video_url:
        st.info("👆 Paste a video URL above to start.")
        return

    if sess.get("video_id"):
        render_player(sess["video_id"])
    else:
        st.video(video_url)

    if sess.get("video_title"):
        st.caption(f"**{sess['video_title']}**")

    st.markdown(
        f"""
        <a href="{video_url}" target="_blank" style="text-decoration:none;">
            <button class="ek-youtube-button">📺 Open in YouTube</button>
        </a>
        """,
        unsafe_allow_html=True,
    )
