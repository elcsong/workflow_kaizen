"""session_manager characterization tests — 리팩토링 안전망."""
from __future__ import annotations

import os
from pathlib import Path


def test_create_new_session_structure(session_manager):
    s = session_manager.create_new_session()
    assert "id" in s and "created_at" in s
    assert s["video_url"] == ""
    assert s["phase1"] == {"notes": "", "missed_parts": ""}
    assert set(s["phase2"].keys()) >= {
        "vocab_issues",
        "grammar_issues",
        "linking_issues",
        "vocab_list",
        "grammar_list",
        "notes",
    }
    assert s["phase3"] == {"audio_file": None, "summary": ""}


def test_save_and_load_roundtrip(session_manager):
    s = session_manager.create_new_session()
    s["video_url"] = "https://youtu.be/abc"
    s["phase1"]["notes"] = "test note"
    session_manager.save_session(s)

    loaded = session_manager.load_session(s["id"])
    assert loaded is not None
    assert loaded["video_url"] == "https://youtu.be/abc"
    assert loaded["phase1"]["notes"] == "test note"


def test_save_assigns_id_when_missing(session_manager):
    s = {"created_at": "2026-01-01", "phase1": {}, "phase2": {}, "phase3": {}}
    session_manager.save_session(s)
    assert s["id"]  # ID가 할당되어야 함


def test_list_sessions_sorted_newest_first(session_manager):
    s1 = session_manager.create_new_session()
    s1["id"] = "20260101_000000"
    s1["created_at"] = "2026-01-01T00:00:00"
    session_manager.save_session(s1)

    s2 = session_manager.create_new_session()
    s2["id"] = "20260301_000000"
    s2["created_at"] = "2026-03-01T00:00:00"
    session_manager.save_session(s2)

    sessions = session_manager.list_sessions()
    assert len(sessions) == 2
    assert sessions[0]["id"] == "20260301_000000"
    assert sessions[1]["id"] == "20260101_000000"


def test_load_nonexistent_returns_none(session_manager):
    assert session_manager.load_session("does_not_exist") is None


def test_delete_removes_json_and_audio(session_manager, tmp_data_dir: Path):
    s = session_manager.create_new_session()
    session_manager.save_session(s)
    session_manager.save_audio(s["id"], b"fake audio bytes")

    json_path = tmp_data_dir / "sessions" / f"{s['id']}.json"
    audio_path = tmp_data_dir / "audio" / f"{s['id']}_recording.wav"
    assert json_path.exists() and audio_path.exists()

    assert session_manager.delete_session(s["id"]) is True
    assert not json_path.exists()
    assert not audio_path.exists()
