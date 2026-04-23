"""YouTube 비디오 ID 추출과 메타데이터 조회.

Sprint 1 범위: 순수 URL 파싱 함수만 이동. yt-dlp·transcript API 호출 부분은
후속 Sprint에서 캐시와 함께 옮긴다.
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


def extract_video_id_from_url(url: str | None) -> str | None:
    """다양한 YouTube URL 형식에서 11자리 video ID를 추출."""
    if not url:
        return None
    for pattern in _YOUTUBE_ID_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
