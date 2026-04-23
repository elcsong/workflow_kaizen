"""커스텀 YouTube 플레이어 — 트랜스포트 컨트롤 + 루프 기능."""
from __future__ import annotations


def build_player_html(video_id: str) -> str:
    """플레이어 iframe HTML을 빌드 (테스트 가능한 순수 함수).

    Streamlit의 components.html 호출은 호출자가 담당.
    """
    return f"""
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
            <button onclick="toggleLoop()" id="loopBtn" style="padding:8px 16px;cursor:pointer;border-radius:5px;border:1px solid #ccc;background:#f0f0f0;">🔁 Loop</button>
            <input type="number" id="loopDur" value="5" min="1" max="30" step="0.5" style="width:55px;padding:8px 4px;border-radius:5px;border:1px solid #ccc;text-align:center;font-size:14px;"/>
            <span style="font-family:sans-serif;font-size:14px;">s</span>
        </div>

        <script>
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
                    events: {{ 'onStateChange': onPlayerStateChange }}
                }});
            }}

            function onPlayerStateChange(event) {{}}

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
                    if (state == 1) {{ player.pauseVideo(); }} else {{ player.playVideo(); }}
                }}
            }}

            function toggleLoop() {{
                if (!player || !player.getCurrentTime) return;
                isLooping = !isLooping;
                var btn = document.getElementById("loopBtn");
                if (isLooping) {{
                    var loopDuration = parseFloat(document.getElementById("loopDur").value) || 5;
                    btn.innerHTML = "🔁 Stop Loop";
                    btn.style.background = "#ffcccc";
                    btn.style.borderColor = "#ff0000";
                    var curr = player.getCurrentTime();
                    loopStart = Math.max(0, curr - loopDuration);
                    player.seekTo(loopStart);
                    player.playVideo();
                    if (loopInterval) clearInterval(loopInterval);
                    loopInterval = setInterval(checkLoop, 200);
                }} else {{
                    btn.innerHTML = "🔁 Loop";
                    btn.style.background = "#f0f0f0";
                    btn.style.borderColor = "#ccc";
                    if (loopInterval) clearInterval(loopInterval);
                }}
            }}

            function checkLoop() {{
                if (!isLooping) return;
                var curr = player.getCurrentTime();
                var loopDuration = parseFloat(document.getElementById("loopDur").value) || 5;
                if (curr >= loopStart + loopDuration) {{
                    player.seekTo(loopStart);
                }}
            }}
        </script>
    </body>
    </html>
    """


def render_custom_player(video_id: str, components_module) -> None:
    """주어진 video_id로 플레이어를 렌더 (components.html 호출)."""
    components_module.html(build_player_html(video_id), height=420)
