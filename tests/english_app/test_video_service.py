"""video 서비스 characterization tests — URL 파서."""
from __future__ import annotations

import pytest

from english_app.services.video import extract_video_id_from_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        (
            "https://www.youtube.com/watch?feature=share&v=dQw4w9WgXcQ",
            "dQw4w9WgXcQ",
        ),
    ],
)
def test_extract_video_id_known_formats(url: str, expected: str):
    assert extract_video_id_from_url(url) == expected


def test_extract_video_id_none_on_invalid():
    assert extract_video_id_from_url("https://example.com/") is None
    assert extract_video_id_from_url("") is None
    assert extract_video_id_from_url(None) is None


def test_extract_video_id_returns_eleven_char_id():
    vid = extract_video_id_from_url("https://youtu.be/abc123DEF_-")
    assert vid is not None
    assert len(vid) == 11
