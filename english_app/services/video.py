"""YouTube 비디오 ID 추출과 메타데이터 조회.

- `extract_video_id_from_url`: 순수 URL 파서.
- `fetch_video_info`: yt-dlp + oEmbed fallback + transcript API 통합 호출.
"""
from __future__ import annotations

import logging
import re
from typing import Final

logger = logging.getLogger(__name__)

_YOUTUBE_ID_PATTERNS: Final[tuple[str, ...]] = (
    r"(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})",
    r"youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})",
)

_YDL_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "nocheckcertificate": True,
    "noplaylist": True,
    "extract_flat": False,
    "http_headers": {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        ),
    },
}


def extract_video_id_from_url(url: str | None) -> str | None:
    """다양한 YouTube URL 형식에서 11자리 video ID를 추출."""
    if not url:
        return None
    for pattern in _YOUTUBE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_video_info(url: str) -> tuple[str, str, str | None]:
    """`(title, transcript, video_id)` 반환.

    - yt-dlp `noplaylist=True` 로 단일 영상 추출
    - 플레이리스트 응답 시 `entries[0]` 폴백
    - 실패 시 oEmbed API 로 title 만이라도 복구
    - transcript는 `youtube_transcript_api` 로 영문 자막 우선
    """
    if not url:
        return "", "", None

    title = url
    transcript_text = ""
    video_id: str | None = None

    try:
        import yt_dlp  # 지연 임포트 — 테스트에서 mock 가능
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            info = ydl.extract_info(url, download=False)
            if isinstance(info, dict) and info.get("_type") == "playlist":
                entries = info.get("entries") or []
                info = entries[0] if entries else info
            title = (info.get("title") if isinstance(info, dict) else None) or url
            video_id = info.get("id") if isinstance(info, dict) else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("yt-dlp error: %s", exc)

    if (not title or title == url) and url:
        try:
            import requests
            oembed = requests.get(
                "https://www.youtube.com/oembed",
                params={"url": url, "format": "json"},
                timeout=3,
            )
            if oembed.status_code == 200:
                title = oembed.json().get("title", title) or title
        except Exception as exc:  # noqa: BLE001
            logger.warning("oembed fallback error: %s", exc)

    if not video_id:
        video_id = extract_video_id_from_url(url)

    if video_id:
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            data = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
            transcript_text = " ".join(item.text for item in data)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Transcript error: %s", exc)
            transcript_text = ""

    return title, transcript_text, video_id
