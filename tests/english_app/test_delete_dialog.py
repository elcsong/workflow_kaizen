"""삭제 모달 분기 로직."""
from __future__ import annotations

from unittest.mock import MagicMock

from english_app.ui.components.delete_dialog import confirm_or_cancel


def test_confirm_invokes_callback():
    cb = MagicMock()
    called = confirm_or_cancel(
        confirmed=True, on_confirm=cb, session_id="abc"
    )
    assert called is True
    cb.assert_called_once_with("abc")


def test_cancel_does_not_invoke():
    cb = MagicMock()
    called = confirm_or_cancel(
        confirmed=False, on_confirm=cb, session_id="abc"
    )
    assert called is False
    cb.assert_not_called()
