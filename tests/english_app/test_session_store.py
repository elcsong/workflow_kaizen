"""세션 인덱싱 검증."""
from __future__ import annotations

import json
from pathlib import Path

from english_app.services.session_store import (
    INDEX_FILENAME,
    load_index,
    rebuild_index,
    remove_entry,
    upsert_entry,
)


def _write_session(sessions_dir: Path, sid: str, created: str, **fields):
    payload = {
        "id": sid,
        "created_at": created,
        "video_url": fields.get("video_url", ""),
        "video_title": fields.get("video_title", ""),
        "phase1": fields.get("phase1", {}),
        "phase2": fields.get("phase2", {}),
        "phase3": fields.get("phase3", {}),
    }
    (sessions_dir / f"{sid}.json").write_text(json.dumps(payload), encoding="utf-8")
    return payload


def test_rebuild_index_creates_file_and_returns_entries(tmp_path: Path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    _write_session(sessions, "20260101_000000", "2026-01-01T00:00:00")
    _write_session(sessions, "20260301_000000", "2026-03-01T00:00:00")

    entries = rebuild_index(sessions)
    assert len(entries) == 2
    assert entries[0].id == "20260301_000000"  # 최신 우선
    assert (sessions / INDEX_FILENAME).exists()


def test_load_index_uses_existing_file_without_scanning(tmp_path: Path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    _write_session(sessions, "20260101_000000", "2026-01-01T00:00:00")
    rebuild_index(sessions)

    # 인덱스만 남기고 JSON 파일 삭제
    (sessions / "20260101_000000.json").unlink()

    entries = load_index(sessions)
    assert len(entries) == 1  # 인덱스만 읽으므로 데이터 그대로 반환


def test_upsert_entry_updates_index(tmp_path: Path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    payload = _write_session(sessions, "20260101_000000", "2026-01-01T00:00:00")
    rebuild_index(sessions)

    payload["video_title"] = "Updated Title"
    upsert_entry(sessions, payload)

    entries = load_index(sessions)
    assert entries[0].video_title == "Updated Title"


def test_remove_entry_drops_from_index(tmp_path: Path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    _write_session(sessions, "a", "2026-01-01")
    _write_session(sessions, "b", "2026-02-01")
    rebuild_index(sessions)

    remove_entry(sessions, "a")
    entries = load_index(sessions)
    assert {e.id for e in entries} == {"b"}


def test_progress_label_from_phase_completion(tmp_path: Path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    _write_session(
        sessions,
        "complete",
        "2026-01-01",
        phase1={"notes": "n"},
        phase2={"grammar_issues": "g"},
        phase3={"summary": "s"},
    )
    _write_session(sessions, "blank", "2026-01-02")

    entries = {e.id: e for e in rebuild_index(sessions)}
    assert entries["complete"].progress_pct == 100
    assert entries["blank"].progress_pct == 0
