import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from session_manager import SessionManager
from llm_helper import get_ai_explanation, MODELS

# Page Configuration
st.set_page_config(
    page_title="English Kaizen",
    page_icon="🎧",
    layout="wide"
)

# Initialize Manager
if 'manager' not in st.session_state:
    st.session_state.manager = SessionManager()

# --- Tooltip Constants ---
TIPS = {
    "phase1": """
    **✅ 1부: 제대로 듣기 (Proper Listening)**
    
    * **Step 1: 일단 그냥 듣기** (전체 흐름 파악, 60-80% 이해 목표)
    * **Step 2: 노트 테이킹** (중심 내용, 키워드 위주 기록)
    * **Step 3: 다시 듣기** (놓친 부분 체크)
    """,
    "p1_step2": """**Step 2: 뼈대 잡기 (Note Taking)**\n\n**자막 OFF**\n\n전체적인 흐름과 큰 구조(서론, 본론, 결론)를 파악하는 단계입니다. 즉, **'전체 숲'**을 그리는 과정입니다.\n\n들리는 대로 중심 내용을 적어 내려가되, 안 들리는 부분은 집착하지 말고 과감히 넘어갑니다.\n\n(마음가짐: "무슨 이야기를 하는 거지?")""",
    "p1_step3": """**Step 3: 살 붙이기 (Fill in the blanks)**\n\n**자막 OFF (절대 켜지 않음)**\n\nStep 2에서 작성한 노트를 보며 **'놓친 정보(나무)'**를 채워 넣습니다. 딕테이션처럼 모든 단어를 적는 것이 아니라, 핵심 의미를 완성하는 것이 목표입니다.\n\n**[비교 예시]**\n*"What I really want to emphasize here is that consistency is the key to success."*\n\n❌ **딕테이션:** What, I, really, want... (모든 단어/전치사 집착)\n✅ **Step 3:** Consistency -> Success (핵심 정보만!)\n\nStep 3는 '안 들리는 소리'가 아니라 **'놓친 정보'**를 채우는 과정입니다. "아까 놓친 중요한 단어가 뭐였지?"에만 집중하세요.""",
    
    "phase2": """
    **✅ 2부: 원인 분석 및 학습 (Analysis & Learning)**
    
    * **Step 4: 직해 및 비교** (자막 켜고 노트와 비교)
    * **Step 5: 원인 분석** (단어, 문법, 연음 분석)
    * **Step 6: 재확인** (자막 끄고 다시 듣기)
    """,
    "p2_step5_vocab": "**Vocabulary Issues**\n중심 내용 파악에 필수적인 단어(필수 동사, 핵심 명사) 중 몰랐던 것을 정리합니다. 단순 뜻뿐만 아니라 어원이나 예문을 찾아보며 감각을 익히세요.",
    "p2_step5_grammar": "**Grammar & Structure**\n해석이 안 되거나 꼬였던 문장의 구조를 분석합니다. Chat GPT에게 해당 문장의 문법적 쓰임새를 물어보며 깊이 있게 이해하세요.",
    "p2_step5_linking": "**Linking & Pronunciation**\n아는 단어인데 소리가 뭉개져서 안 들린 부분을 적습니다. 연음(Linking) 현상을 파악하고 직접 소리 내어 발음해 보세요.",
    "p2_step5_notes": "**General Analysis Notes**\n위 항목 외에 전체적인 분석 내용이나 느낀 점, 반복해서 틀리는 패턴 등을 자유롭게 기록합니다.",

    "phase3": """
    **✅ 3부: 섀도잉 및 활용 (Shadowing & Utilization)**
    
    * **Step 7: 오답 정리** (최종 복습)
    * **Step 8: 섀도잉** (원어민 억양/속도 복제)
    * **Step 9: 녹음** (내 목소리 비교)
    * **Step 10: 아웃풋** (내 말로 요약하기)
    """,
    "p3_step9": "**Step 9: Recording**\n섀도잉 한 부분을 직접 녹음하여 들어봅니다. 원어민의 발음, 인토네이션, 속도와 자신의 녹음본을 비교하며 스스로 부족한 부분을 체크하고 교정합니다. (전체 영상이 아닌 좋아하는 1~3분 구간만이라도 충분합니다.)",
    "p3_step10": "**Step 10: Summary Output**\n학습한 내용을 바탕으로 자신의 언어(목소리)로 요약해서 말해봅니다. 배운 표현을 응용하고 내 것으로 만듭니다."
}

# --- Helper Functions ---
def get_progress_stats(session):
    """Calculate progress stage and percentage."""
    p1 = session.get("phase1", {})
    p2 = session.get("phase2", {})
    p3 = session.get("phase3", {})
    
    # Check completion of key milestones
    has_notes = bool(p1.get("notes") or p1.get("missed_parts"))
    # Phase 2 completion check updated for new fields
    has_analysis = bool(
        p2.get("vocab_issues") or 
        p2.get("grammar_issues") or 
        p2.get("linking_issues") or 
        p2.get("vocab_list") or
        p2.get("grammar_list")
    )
    has_output = bool(p3.get("summary") or p3.get("audio_file"))
    
    if has_notes and has_analysis and has_output:
        return "Completed", 100, "✅"
    elif has_analysis:
        return "Phase 3: Output", 66, "🗣️"
    elif has_notes:
        return "Phase 2: Analysis", 33, "📝"
    else:
        return "Phase 1: Listening", 0, "👂"

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
    st.session_state.is_dirty = False
    st.toast("Session Saved!", icon="💾")

def go_to_dashboard():
    st.session_state.page = "dashboard"
    st.rerun()

def delete_session_callback(session_id):
    """Handles session deletion and UI update."""
    success = st.session_state.manager.delete_session(session_id)
    if success:
        st.toast("Session Deleted", icon="🗑️")
        # If deleting currently active session, go back to dashboard
        if st.session_state.current_session and st.session_state.current_session.get("id") == session_id:
            st.session_state.current_session = None
            st.session_state.page = "dashboard"
        st.rerun()
    else:
        st.error("Failed to delete session.")

def fetch_video_info(url):
    """Extract video title and transcript (if available)."""
    if not url:
        return "", ""
    
    title = url
    transcript_text = ""

    # 1. Get Title via yt-dlp
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', url)
            video_id = info.get('id')
    except Exception as e:
        print(f"yt-dlp error: {e}")
        video_id = None

    # 2. Get Transcript via youtube_transcript_api
    if video_id:
        try:
            # Prefer manually created English subtitles, fallback to auto-generated
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # Try to find English (manual or auto)
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US', 'en-GB'])
            except:
                # Fallback to generated English if specific codes fail, or just first available
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                except:
                     # Last resort: just take the first one available (could be non-English but better than nothing?)
                     # Or maybe stop here. Let's try to get translation to English if source is different.
                     transcript = transcript_list.find_transcript(['en']).translate('en')

            final_transcript = transcript.fetch()

            # Combine into single string
            transcript_text = " ".join([item['text'] for item in final_transcript])
            
        except Exception as e:
            print(f"Transcript error: {e}")
            transcript_text = ""

    return title, transcript_text, video_id

def render_custom_player(video_id):
    """
    Render a custom YouTube player with transport controls.
    The player is width-constrained so it covers roughly half the screen.
    """
    player_html = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;text-align:center;">
        <div style="max-width:600px;margin:0 auto;">
            <div id="player"></div>
        </div>

        <div style="display:flex;gap:10px;margin-top:10px;justify-content:center;font-family:sans-serif;">
            <button onclick="seek(-5)" style="padding:8px 16px;cursor:pointer;border-radius:5px;border:1px solid #ccc;background:#f0f0f0;">⏪ -5s</button>
            <button onclick="togglePlay()" style="padding:8px 16px;cursor:pointer;border-radius:5px;border:1px solid #ccc;background:#f0f0f0;">⏯ Play/Pause</button>
            <button onclick="seek(5)" style="padding:8px 16px;cursor:pointer;border-radius:5px;border:1px solid #ccc;background:#f0f0f0;">⏩ +5s</button>
            <button onclick="toggleLoop()" id="loopBtn" style="padding:8px 16px;cursor:pointer;border-radius:5px;border:1px solid #ccc;background:#f0f0f0;">🔁 Loop Last 5s</button>
        </div>

        <script>
            // 2. This code loads the IFrame Player API code asynchronously.
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

            var player;
            var isLooping = false;
            var loopStart = 0;
            var loopInterval;

            function onYouTubeIframeAPIReady() {{
                player = new YT.Player('player', {{
                    height: '337',
                    width: '100%',
                    videoId: '{video_id}',
                    playerVars: {{
                        'playsinline': 1,
                        'modestbranding': 1,
                        'rel': 0
                    }},
                    events: {{
                        'onStateChange': onPlayerStateChange
                    }}
                }});
            }}

            function onPlayerStateChange(event) {{
                // Handle state changes if needed
            }}

            function seek(seconds) {{
                if (player && player.getCurrentTime) {{
                    var currentTime = player.getCurrentTime();
                    player.seekTo(currentTime + seconds, true);
                    player.playVideo();
                }}
            }}

            function togglePlay() {{
                if (player && player.getPlayerState) {{
                    var state = player.getPlayerState();
                    if (state == 1) {{ // Playing
                        player.pauseVideo();
                    }} else {{
                        player.playVideo();
                    }}
                }}
            }}
            
            function toggleLoop() {{
                if (!player || !player.getCurrentTime) return;

                isLooping = !isLooping;
                var btn = document.getElementById("loopBtn");
                
                if (isLooping) {{
                    btn.innerHTML = "🔁 Stop Loop";
                    btn.style.background = "#ffcccc";
                    btn.style.borderColor = "#ff0000";
                    
                    // Set loop range: Current Time - 5s to Current Time
                    var curr = player.getCurrentTime();
                    loopStart = Math.max(0, curr - 5);
                    
                    player.seekTo(loopStart);
                    player.playVideo();
                    
                    // Start checking time
                    if (loopInterval) clearInterval(loopInterval);
                    loopInterval = setInterval(checkLoop, 200); // Check frequently
                }} else {{
                    btn.innerHTML = "🔁 Loop Last 5s";
                    btn.style.background = "#f0f0f0";
                    btn.style.borderColor = "#ccc";
                    if (loopInterval) clearInterval(loopInterval);
                }}
            }}
            
            function checkLoop() {{
                if (!isLooping) return;
                
                var curr = player.getCurrentTime();
                // Loop is fixed 5 seconds from start
                if (curr >= loopStart + 5) {{
                    player.seekTo(loopStart);
                }}
            }}
        </script>
    </body>
    </html>
    """
    components.html(player_html, height=420)

# --- Router Logic ---
if 'page' not in st.session_state:
    st.session_state.page = "dashboard"

if 'current_session' not in st.session_state:
    st.session_state.current_session = None

# ==========================================
# VIEW: DASHBOARD
# ==========================================
if st.session_state.page == "dashboard":
    st.title("English Kaizen Dashboard 📊")
    
    # Fetch Data
    sessions = st.session_state.manager.list_sessions()
    
    # Calculate Metrics
    total_sessions = len(sessions)
    completed_count = 0
    in_progress_count = 0
    
    active_sessions = []
    
    for sess in sessions:
        stage, pct, icon = get_progress_stats(sess)
        sess['stage_label'] = stage
        sess['progress_pct'] = pct
        sess['icon'] = icon
        
        if pct == 100:
            completed_count += 1
        else:
            in_progress_count += 1
            active_sessions.append(sess)
            
    # 1. Top Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sessions", total_sessions)
    col2.metric("Completed", completed_count)
    col3.metric("In Progress", in_progress_count)
    
    st.divider()
    
    # 2. Quick Actions
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("➕ Start New Session", type="primary", use_container_width=True):
            create_new_session()
            
    st.write("")

    # 3. In Progress Section (Grid Layout)
    if active_sessions:
        st.subheader("🚀 Continue Learning")
        
        # Display as cards (3 per row)
        cols = st.columns(3)
        for idx, sess in enumerate(active_sessions):
            with cols[idx % 3]:
                with st.container(border=True):
                    st.write(f"**{sess['icon']} {sess['stage_label']}**")
                    
                    # Display Title instead of URL if available
                    display_title = sess.get('video_title') or sess.get('video_url', 'No Video')
                    if len(display_title) > 40:
                        display_title = display_title[:40] + "..."
                        
                    st.caption(f"📅 {sess['created_at'][:10]}")
                    st.text(f"{display_title}")
                    st.progress(sess['progress_pct'])
                    
                    b1, b2 = st.columns([3, 1])
                    with b1:
                        if st.button("Resume", key=f"resume_{sess['id']}", use_container_width=True):
                            load_session(sess['id'])
                    with b2:
                        if st.button("🗑️", key=f"del_card_{sess['id']}", help="Delete Session"):
                            delete_session_callback(sess['id'])

    else:
        st.info("No active sessions. Start a new one!")

    st.divider()

    # 4. History Table
    st.subheader("📜 Learning History")
    
    if sessions:
        # Prepare DataFrame for clean table
        table_data = []
        for sess in sessions:
            # Determine display title
            v_title = sess.get('video_title') or sess.get('video_url', '-')
            if len(v_title) > 50:
                v_title = v_title[:50] + "..."

            table_data.append({
                "Date": sess['created_at'][:10],
                "Stage": f"{sess['icon']} {sess['stage_label']}",
                "Video": v_title,
                "ID": sess['id'] # Hidden but needed for ID
            })
        
        df = pd.DataFrame(table_data)
        
        # Show clickable list manually for better control than st.dataframe
        for index, row in df.iterrows():
            c1, c2, c3, c4, c5 = st.columns([2, 3, 4, 2, 1])
            with c1: st.write(row['Date'])
            with c2: st.write(row['Stage'])
            with c3: st.write(row['Video'])
            with c4:
                if st.button("Open", key=f"hist_{row['ID']}"):
                    load_session(row['ID'])
            with c5:
                if st.button("🗑️", key=f"del_hist_{row['ID']}"):
                     delete_session_callback(row['ID'])
            st.divider()
            
    else:
        st.write("No history yet.")

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
        if st.button("🗑️ Delete Session", type="secondary", use_container_width=True):
            delete_session_callback(sess['id'])
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        video_url = st.text_input(
            "Video URL", 
            value=sess.get("video_url", ""),
            placeholder="Paste YouTube or TED link here..."
        )
        if video_url != sess.get("video_url", ""):
            sess["video_url"] = video_url
            
            # Auto-fetch title when URL changes
            with st.spinner("Fetching video info & transcript..."):
                title, transcript, v_id = fetch_video_info(video_url)
                sess["video_title"] = title
                sess["video_transcript"] = transcript
                sess["video_id"] = v_id
                
            st.session_state.is_dirty = True
            st.rerun()
    
    with col2:
        st.write("")
        st.write("") 
        if st.button("💾 Save Progress", type="primary", use_container_width=True):
            save_current_session()

    # Video Area
    if video_url:
        if sess.get("video_id"):
            render_custom_player(sess["video_id"])
        else:
            st.video(video_url)
        
        if sess.get("video_title"):
            st.caption(f"Playing: **{sess['video_title']}**")

        st.markdown(
            f"""
            <a href="{video_url}" target="_blank" style="text-decoration:none;">
                <button style="background-color: #FF0000; color: white; border: none; border-radius: 5px; padding: 8px 16px; cursor: pointer; font-weight: bold; display: flex; align-items: center; gap: 8px;">
                    📺 Watch on YouTube (New Tab) - Use for Premium/No Ads
                </button>
            </a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("👆 Paste a video URL above to start.")

    st.divider()

    # Tabs
    t1, t2, t3 = st.tabs(["1️⃣ Proper Listening", "2️⃣ Analysis & Learning", "3️⃣ Shadowing & Utilization"])

    # --- Tab 1: Proper Listening (Steps 1-3) ---
    with t1:
        st.subheader("Phase 1: Proper Listening (Steps 1-3)", help=TIPS["phase1"])
        
        st.markdown("""
        * **Step 1: Just Listen** (04:40) - Relax and grasp the context (No input needed).
        """)
        
        # Step 2 and Step 3 in 1 row, 2 columns
        col_s2, col_s3 = st.columns(2)
        
        with col_s2:
            # Step 2 Input
            val = st.text_area(
                "Step 2: Note Taking (Main Ideas)", 
                value=sess["phase1"].get("notes", ""), 
                height=400,
                help=TIPS["p1_step2"],
                key="p1_step2_notes"
            )
            if val != sess["phase1"].get("notes", ""):
                sess["phase1"]["notes"] = val
                st.session_state.is_dirty = True
            
            # Button to copy Step 2 notes to Step 3
            if st.button("📥 Copy from Step 2", help="Copy Step 2 notes here to fill in the blanks."):
                new_val = sess["phase1"].get("notes", "")
                sess["phase1"]["missed_parts"] = new_val
                st.session_state["p1_step3_missed"] = new_val
                st.session_state.is_dirty = True
                st.rerun()
        
        with col_s3:
            # Step 3 Input
            val = st.text_area(
                "Step 3: Listen Again (Missed Parts)", 
                value=sess["phase1"].get("missed_parts", ""), 
                height=400,
                help=TIPS["p1_step3"],
                key="p1_step3_missed"
            )
            if val != sess["phase1"].get("missed_parts", ""):
                sess["phase1"]["missed_parts"] = val
                st.session_state.is_dirty = True

    # --- Tab 2: Analysis & Learning (Steps 4-6) ---
    with t2:
        st.subheader("Phase 2: Analysis & Learning (Steps 4-6)", help=TIPS["phase2"])
        
        st.markdown("""
        * **Step 6: Verify** (20:28) - Turn off subtitles and listen again.
        """)

        st.divider()
        
        # --- Step 4 Implementation ---
        st.markdown("### Step 4: Direct Translation (Compare with Notes)")
        st.caption("Turn on subtitles and compare them with your notes from Phase 1.")
        
        c_s4_1, c_s4_2 = st.columns(2)
        with c_s4_1:
            st.text_area(
                "Your Step 2 Notes (Read Only):",
                value=sess["phase1"].get("notes", ""),
                height=200,
                disabled=True,
                key="step4_review_notes"
            )
        with c_s4_2:
            st.text_area(
                "Your Step 3 Missed Parts (Read Only):",
                value=sess["phase1"].get("missed_parts", ""),
                height=200,
                disabled=True,
                key="step4_review_missed"
            )
        
        st.divider()
        st.markdown("### Step 5: Error Analysis (Why did I miss it?)")
        st.caption("Analyze your missed parts by category:")
        
        p2 = sess["phase2"]
        
        # Expander 1: Vocabulary
        with st.expander("📄 Vocabulary Issues (Unknown Words)", expanded=bool(p2.get("vocab_issues"))):
            val = st.text_area(
                "List unknown words & meanings:", 
                value=p2.get("vocab_issues", ""), 
                height=150,
                help=TIPS["p2_step5_vocab"],
                key="input_vocab_issues"
            )
            if val != p2.get("vocab_issues", ""):
                sess["phase2"]["vocab_issues"] = val
                st.session_state.is_dirty = True
                
        # Expander 2: Grammar
        with st.expander("📐 Grammar & Structure (Interpretation)", expanded=True): # Expanded by default for AI feature focus
            col_g1, col_g2 = st.columns([3, 1])
            with col_g1:
                val = st.text_area(
                    "Analyze difficult sentence structures:", 
                    value=p2.get("grammar_issues", ""), 
                    height=150,
                    help=TIPS["p2_step5_grammar"],
                    key="input_grammar_issues"
                )
                if val != p2.get("grammar_issues", ""):
                    sess["phase2"]["grammar_issues"] = val
                    st.session_state.is_dirty = True
            
            with col_g2:
                st.write("")
                st.write("")
                if st.button("🤖 Ask AI to Explain", help="Get explanation for the text above"):
                    if not p2.get("grammar_issues", "").strip():
                        st.warning("Please enter some text to analyze first.")
                    else:
                        with st.spinner(f"Asking {ai_model_name}..."):
                            explanation = get_ai_explanation(
                                p2.get("grammar_issues"), 
                                ai_provider, 
                                selected_model_id,
                                context=sess.get("video_transcript", "")
                            )
                            st.session_state['ai_explanation'] = explanation
            
            # Display AI Result if available
            if 'ai_explanation' in st.session_state:
                st.info(f"**🤖 AI Explanation ({ai_model_name}):**\n\n{st.session_state['ai_explanation']}")
                if st.button("Clear Explanation", key="clear_ai"):
                    del st.session_state['ai_explanation']
                    st.rerun()

        # Expander 3: Linking
        with st.expander("🔊 Linking & Pronunciation (Sound)", expanded=bool(p2.get("linking_issues"))):
            val = st.text_area(
                "Write down sounds you couldn't catch:", 
                value=p2.get("linking_issues", ""), 
            height=150,
                help=TIPS["p2_step5_linking"],
                key="input_linking_issues"
            )
            if val != p2.get("linking_issues", ""):
                sess["phase2"]["linking_issues"] = val
                st.session_state.is_dirty = True
        
        # General Notes
        st.write("")
        val = st.text_area(
            "📝 General Analysis Notes", 
            value=p2.get("notes", ""), 
            height=100,
            help=TIPS["p2_step5_notes"],
            key="p2_general_notes" # Added unique key
        )
        if val != p2.get("notes", ""):
            sess["phase2"]["notes"] = val
            st.session_state.is_dirty = True

        st.divider()
        st.subheader("📚 Personal Knowledge Bank")
        
        # Sub-tabs for Banks
        bank_tab1, bank_tab2 = st.tabs(["Vocabulary Bank", "Grammar Bank"])
        
        with bank_tab1:
            st.caption("Collect unknown words here:")
            current_vocab = p2.get("vocab_list", [])
            if not current_vocab:
                df_vocab = pd.DataFrame(columns=["Word", "Meaning", "Example"])
            else:
                df_vocab = pd.DataFrame(current_vocab)

            edited_df_v = st.data_editor(df_vocab, num_rows="dynamic", use_container_width=True, key="vocab_editor")
            new_vocab = edited_df_v.to_dict('records')
            if new_vocab != current_vocab:
                sess["phase2"]["vocab_list"] = new_vocab
                st.session_state.is_dirty = True

        with bank_tab2:
            st.caption("Collect sentence patterns & grammar points here:")
            current_grammar = p2.get("grammar_list", [])
            if not current_grammar:
                df_grammar = pd.DataFrame(columns=["Sentence/Pattern", "Grammar Point", "My Note"])
            else:
                df_grammar = pd.DataFrame(current_grammar)

            edited_df_g = st.data_editor(df_grammar, num_rows="dynamic", use_container_width=True, key="grammar_editor")
            new_grammar = edited_df_g.to_dict('records')
            if new_grammar != current_grammar:
                sess["phase2"]["grammar_list"] = new_grammar
                st.session_state.is_dirty = True

    # --- Tab 3: Shadowing & Utilization (Steps 7-10) ---
    with t3:
        st.subheader("Phase 3: Shadowing & Utilization (Steps 7-10)", help=TIPS["phase3"])
        
        st.markdown("""
        * **Step 7: Review** (21:23) - Final review of missed parts.
        * **Step 8: Shadowing** (21:35) - Mimic intonation/speed (No input needed).
        """)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🎙️ Step 9: Recording", help=TIPS["p3_step9"])
            audio_val = st.audio_input("Record Shadowing/Summary")
            if audio_val:
                st.audio(audio_val)
                if st.button("Save Recording"):
                    bytes_data = audio_val.read()
                    fname = st.session_state.manager.save_audio(sess["id"], bytes_data)
                    sess["phase3"]["audio_file"] = fname
                    st.success("Saved!")
                    st.session_state.is_dirty = True

            saved = sess["phase3"].get("audio_file")
            if saved:
                st.info(f"Saved: {saved}")
                path = os.path.join("english_app/data/audio", saved)
                if os.path.exists(path):
                    st.audio(path)

        with c2:
            st.markdown("### ✍️ Step 10: Output", help=TIPS["p3_step10"])
            val = st.text_area(
                "Summary (Your Own Words):", 
                value=sess["phase3"].get("summary", ""), 
            height=300,
                key="p3_summary_output" # Added unique key
        )
            if val != sess["phase3"].get("summary", ""):
                sess["phase3"]["summary"] = val
            st.session_state.is_dirty = True
