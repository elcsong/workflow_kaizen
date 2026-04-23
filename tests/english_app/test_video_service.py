"""video 서비스 characterization tests — URL 파서 + fetch."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from english_app.services.video import (
    extract_video_id_from_url,
    fetch_video_info,
)


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


def test_fetch_returns_empty_for_blank_url():
    assert fetch_video_info("") == ("", "", None)


def test_fetch_uses_yt_dlp_title_when_successful():
    fake_info = {"title": "Real Title", "id": "vid12345678"}
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value.extract_info.return_value = fake_info
    fake_ydl.__exit__.return_value = False
    with patch("yt_dlp.YoutubeDL", return_value=fake_ydl), \
         patch("youtube_transcript_api.YouTubeTranscriptApi") as transcript_cls:
        transcript_cls.return_value.fetch.return_value = []
        title, transcript, vid = fetch_video_info("https://youtu.be/vid12345678")
    assert title == "Real Title"
    assert vid == "vid12345678"


def test_fetch_falls_back_to_oembed_when_yt_dlp_fails():
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value.extract_info.side_effect = RuntimeError("blocked")
    fake_ydl.__exit__.return_value = False
    fake_resp = MagicMock(status_code=200)
    fake_resp.json.return_value = {"title": "oEmbed Title"}
    with patch("yt_dlp.YoutubeDL", return_value=fake_ydl), \
         patch("requests.get", return_value=fake_resp), \
         patch("youtube_transcript_api.YouTubeTranscriptApi") as transcript_cls:
        transcript_cls.return_value.fetch.return_value = []
        url = "https://www.youtube.com/watch?v=abc12345678"
        title, _, vid = fetch_video_info(url)
    assert title == "oEmbed Title"
    assert vid == "abc12345678"  # 정규식 fallback


def test_fetch_handles_playlist_response_with_entries():
    playlist = {
        "_type": "playlist",
        "entries": [{"title": "Entry One", "id": "ent12345678"}],
    }
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value.extract_info.return_value = playlist
    fake_ydl.__exit__.return_value = False
    with patch("yt_dlp.YoutubeDL", return_value=fake_ydl), \
         patch("youtube_transcript_api.YouTubeTranscriptApi") as transcript_cls:
        transcript_cls.return_value.fetch.return_value = []
        title, _, vid = fetch_video_info("https://youtu.be/ent12345678")
    assert title == "Entry One"
    assert vid == "ent12345678"
