import logging
import os
import sys

# english_app 패키지 임포트를 위해 프로젝트 루트를 sys.path에 선주입.
# Streamlit이 app.py를 스크립트로 실행하면 english_app/ 만 경로에 들어가기 때문.
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from session_manager import SessionManager
from llm_helper import get_ai_explanation, stream_ai_explanation, MODELS

from english_app.services import session_store
from english_app.services.autosave import should_autosave
from english_app.services.progress import get_progress_stats
from english_app.ui import theme
from english_app.ui.components.dirty_badge import render_dirty_badge
from english_app.ui.components.phase_tabs import (
    render_phase1,
    render_phase2,
    render_phase3,
)
from english_app.ui.components.player import render_custom_player as _render_custom_player_ui
from english_app.ui.dashboard import render_dashboard
from english_app.ui.tips import TIPS

logger = logging.getLogger(__name__)
SESSIONS_PATH = os.path.join(_APP_DIR, "data", "sessions")

# Page Configuration
st.set_page_config(
    page_title="English Kaizen",
    page_icon="🎧",
    layout="wide"
)

# Sprint 4: 디자인 토큰 CSS 주입 (인라인 CSS 제거 → static/tokens.css)
theme.inject_into(st)

# Initialize Manager
if 'manager' not in st.session_state:
    st.session_state.manager = SessionManager()

# Sprint 3 신규 상태 키 디폴트
st.session_state.setdefault('auto_save_enabled', False)
st.session_state.setdefault('dirty_since', None)
st.session_state.setdefault('pending_delete', None)
st.session_state.setdefault('rerun_count', 0)
st.session_state.setdefault('onboarding_dismissed', False)
st.session_state.rerun_count += 1


@st.cache_data(ttl=3600, show_spinner=False)
def cached_video_info(url: str):
    """Sprint 3: yt-dlp + transcript 호출 결과 캐시 (TTL 1h)."""
    return fetch_video_info(url)


def list_sessions_indexed():
    """대시보드용 — 인덱스 파일만 읽어 빠르게 조회."""
    from pathlib import Path
    return session_store.load_index(Path(SESSIONS_PATH))


def mark_dirty():
    """text_area on_change 콜백 — Dirty 시점 기록 + rerun 회피."""
    import time as _t
    st.session_state.is_dirty = True
    if st.session_state.dirty_since is None:
        st.session_state.dirty_since = _t.monotonic()


def clear_dirty():
    st.session_state.is_dirty = False
    st.session_state.dirty_since = None

# Sprint 4: TIPS / get_progress_stats 는 ui/tips.py · services/progress.py 로 이동.

def load_session(session_id):
    st.session_state.current_session = st.session_state.manager.load_session(session_id)
    st.session_state.page = "learning"
    st.session_state.is_dirty = False
    st.rerun()

def create_new_session():
    st.session_state.current_session = st.session_state.manager.create_new_session()
    st.session_state.page = "learning"
    st.session_state.is_dirty = False
    st.rerun()

def save_current_session():
    st.session_state.manager.save_session(st.session_state.current_session)
    # 인덱스 즉시 갱신 (Sprint 3)
    from pathlib import Path
    session_store.upsert_entry(
        Path(SESSIONS_PATH), st.session_state.current_session
    )
    clear_dirty()
    st.toast("Session Saved!", icon="💾")

def go_to_dashboard():
    st.session_state.page = "dashboard"
    # Note: st.rerun() not needed when used as on_click callback

def _do_delete(session_id: str):
    """실제 삭제 수행 (모달 confirm 후)."""
    success = st.session_state.manager.delete_session(session_id)
    if success:
        from pathlib import Path
        session_store.remove_entry(Path(SESSIONS_PATH), session_id)
        st.toast("Session Deleted", icon="🗑️")
        if (
            st.session_state.current_session
            and st.session_state.current_session.get("id") == session_id
        ):
            st.session_state.current_session = None
            st.session_state.page = "dashboard"
        st.session_state.pending_delete = None
        st.rerun()
    else:
        st.error("Failed to delete session.")


def request_delete(session_id: str):
    """Sprint 3: 즉시 삭제 대신 확인 모달 큐에 등록."""
    st.session_state.pending_delete = session_id


def delete_session_callback(session_id):
    """레거시 즉시 삭제 — 모달 확정 시에만 호출."""
    _do_delete(session_id)


@st.dialog("세션 삭제 확인")
def _delete_confirmation_dialog(session_id: str):
    st.warning(
        f"세션 `{session_id}`를 삭제합니다. 이 작업은 되돌릴 수 없습니다."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✅ 삭제", type="primary", use_container_width=True):
            _do_delete(session_id)
    with col_b:
        if st.button("❌ 취소", use_container_width=True):
            st.session_state.pending_delete = None
            st.rerun()

from english_app.services.video import extract_video_id_from_url  # noqa: E402

def fetch_video_info(url):
    """Extract video title and transcript (if available)."""
    if not url:
        return "", "", None

    title = url
    transcript_text = ""
    video_id = None

    # 1. Get Title via yt-dlp (noplaylist=True: &list= 플레이리스트 URL도 단일 영상으로 처리)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'noplaylist': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # 플레이리스트 응답 방어 — entries[0] 우선
            if isinstance(info, dict) and info.get('_type') == 'playlist':
                entries = info.get('entries') or []
                info = entries[0] if entries else info
            title = info.get('title') or url
            video_id = info.get('id')
    except Exception as e:
        logger.warning("yt-dlp error: %s", e)

    # 1b. yt-dlp 실패 시 oembed API fallback (title만이라도)
    if (not title or title == url) and url:
        try:
            import requests as _r
            oembed = _r.get(
                "https://www.youtube.com/oembed",
                params={"url": url, "format": "json"},
                timeout=3,
            )
            if oembed.status_code == 200:
                title = oembed.json().get("title", title) or title
        except Exception as e:  # noqa: BLE001
            logger.warning("oembed fallback error: %s", e)

    # video_id가 비어 있으면 URL 정규식으로 추출 시도 (services/video 재사용)
    if not video_id:
        video_id = extract_video_id_from_url(url)

    # 2. Get Transcript via youtube_transcript_api (new API)
    if video_id:
        try:
            api = YouTubeTranscriptApi()
            transcript_data = api.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
            transcript_text = " ".join([item.text for item in transcript_data])
        except Exception as e:
            logger.warning("Transcript error: %s", e)
            transcript_text = ""

    return title, transcript_text, video_id

def render_custom_player(video_id):
    """Sprint 4: ui/components/player.py 로 이동된 빌더에 위임."""
    _render_custom_player_ui(video_id, components)

# --- Router Logic ---
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

# Sprint 3: 모달이 큐에 등록되어 있으면 먼저 노출
if st.session_state.pending_delete:
    _delete_confirmation_dialog(st.session_state.pending_delete)

# Sprint 3: Dirty 배지 (학습 모드에서만 의미 있음)
if st.session_state.get("is_dirty"):
    render_dirty_badge(True, st)

# Sprint 3: 자동저장 정책 평가
_decision = should_autosave(
    is_dirty=bool(st.session_state.get("is_dirty")),
    auto_save_enabled=bool(st.session_state.get("auto_save_enabled")),
    dirty_since=st.session_state.get("dirty_since"),
)
if _decision.should_save and st.session_state.get("current_session"):
    save_current_session()

# ==========================================
# VIEW: DASHBOARD
# ==========================================
if st.session_state.page == "dashboard":
    indexed = list_sessions_indexed()
    sessions = [
        {
            "id": e.id,
            "created_at": e.created_at,
            "video_url": e.video_url,
            "video_title": e.video_title,
            "phase1": {},
            "phase2": {},
            "phase3": {},
            "stage_label": e.stage_label,
            "progress_pct": e.progress_pct,
        }
        for e in indexed
    ]
    if not sessions:
        sessions = st.session_state.manager.list_sessions()

    def _on_dismiss():
        st.session_state.onboarding_dismissed = True

    render_dashboard(
        st=st,
        sessions=sessions,
        onboarding_dismissed=st.session_state.onboarding_dismissed,
        on_onboarding_dismiss=_on_dismiss,
        on_create_new=create_new_session,
        on_resume=load_session,
        on_request_delete=request_delete,
    )

# ==========================================
# VIEW: LEARNING MODE (Active Session)
# ==========================================
elif st.session_state.page == "learning":
    sess = st.session_state.current_session
    
    # Sidebar
    with st.sidebar:
        st.button("🔙 Back to Dashboard", on_click=go_to_dashboard, use_container_width=True)
        st.divider()
        st.caption(f"Session ID: {sess['id']}")
        st.caption(f"Date: {sess['created_at'][:10]}")
        
        # Show Title in Sidebar
        if sess.get("video_title"):
            st.info(f"📺 {sess['video_title']}")
        
        st.divider()
        st.subheader("🤖 AI Tutor Settings")
        
        # AI Provider Selection
        ai_provider = st.selectbox("Select Provider", list(MODELS.keys()))
        
        # Model Selection based on Provider
        if ai_provider:
            model_options = MODELS[ai_provider]
            ai_model_name = st.selectbox(
                "Select Model", 
                list(model_options.keys())
            )
            # Store actual API model ID
            selected_model_id = model_options[ai_model_name]
        
        st.divider()
        # Sprint 3: 자동저장 토글 (디폴트 off)
        st.session_state.auto_save_enabled = st.toggle(
            "💾 자동 저장 (3초)",
            value=st.session_state.auto_save_enabled,
            help="Dirty 상태가 3초 이상 지속되면 자동 저장합니다.",
        )
        st.caption(f"🔁 Reruns this session: {st.session_state.rerun_count}")

        st.divider()
        if st.button("🗑️ Delete Session", type="secondary", use_container_width=True):
            request_delete(sess['id'])
            st.rerun()
    
    # ===== Split Layout: Left = Video, Right = Tabs =====
    left_col, right_col = st.columns([1, 2])  # Video 1/3, Tabs 2/3
    
    # --- LEFT COLUMN: Video Area ---
    with left_col:
        video_url = st.text_input(
            "Video URL", 
            value=sess.get("video_url", ""),
            placeholder="Paste YouTube link here..."
        )
        if video_url and video_url != sess.get("video_url", ""):
            sess["video_url"] = video_url
            # Sprint 3: 캐시된 fetcher 사용 — 동일 URL 재호출 회피
            with st.spinner("Fetching video info & transcript..."):
                title, transcript, v_id = cached_video_info(video_url)
                sess["video_title"] = title
                sess["video_transcript"] = transcript
                sess["video_id"] = v_id
            mark_dirty()
            st.rerun()
        
        col_save, col_refresh = st.columns([3, 1])
        with col_save:
            if st.button("💾 Save Progress", type="primary", use_container_width=True):
                save_current_session()
        with col_refresh:
            if st.button("🔄", help="비디오 메타데이터 다시 가져오기 (제목·자막)", use_container_width=True):
                cached_video_info.clear()
                if video_url:
                    with st.spinner("Re-fetching video info..."):
                        title, transcript, v_id = cached_video_info(video_url)
                        sess["video_title"] = title
                        sess["video_transcript"] = transcript
                        sess["video_id"] = v_id
                    mark_dirty()
                    st.toast("메타데이터 갱신 완료. 저장 버튼을 눌러 반영하세요.", icon="🔄")
                    st.rerun()

        st.divider()
        
        # Video Player
        if video_url:
            if sess.get("video_id"):
                render_custom_player(sess["video_id"])
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
        else:
            st.info("👆 Paste a video URL above to start.")
    
    # --- RIGHT COLUMN: Tabs Area ---
    with right_col:
        t1, t2, t3 = st.tabs(["1️⃣ Listening", "2️⃣ Analysis", "3️⃣ Shadowing"])

    # --- Tab 1: Proper Listening (Steps 1-3) ---
    with t1:
        render_phase1(st=st, sess=sess, on_dirty=mark_dirty)

    # --- Tab 2: Analysis & Learning (Steps 4-6) ---
    with t2:
        render_phase2(
            st=st,
            sess=sess,
            on_dirty=mark_dirty,
            ai_provider=ai_provider,
            ai_model_name=ai_model_name,
            selected_model_id=selected_model_id,
            stream_ai_explanation=stream_ai_explanation,
            transcript_api=YouTubeTranscriptApi,
        )

    # --- Tab 3: Shadowing & Utilization (Steps 7-10) ---
    with t3:
        render_phase3(
            st=st,
            sess=sess,
            on_dirty=mark_dirty,
            save_audio=st.session_state.manager.save_audio,
            audio_dir=os.path.join(_APP_DIR, "data", "audio"),
        )
