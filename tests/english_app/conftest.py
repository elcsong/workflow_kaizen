"""english_app 공유 테스트 fixture."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# english_app 패키지를 import 가능하게 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """세션 I/O용 임시 데이터 디렉토리 (세션·오디오·비디오 하위 포함)."""
    (tmp_path / "sessions").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "videos").mkdir()
    return tmp_path


@pytest.fixture
def session_manager(tmp_data_dir: Path, monkeypatch: pytest.MonkeyPatch):
    """임시 디렉토리로 격리된 SessionManager 인스턴스."""
    monkeypatch.setattr(
        "english_app.session_manager.SESSIONS_DIR",
        str(tmp_data_dir / "sessions"),
    )
    monkeypatch.setattr(
        "english_app.session_manager.AUDIO_DIR",
        str(tmp_data_dir / "audio"),
    )
    monkeypatch.setattr(
        "english_app.session_manager.VIDEO_DIR",
        str(tmp_data_dir / "videos"),
    )
    from english_app.session_manager import SessionManager

    return SessionManager()
