"""자동저장 결정 함수 검증."""
from __future__ import annotations

from english_app.services.autosave import should_autosave


def test_disabled_returns_false():
    d = should_autosave(
        is_dirty=True, auto_save_enabled=False, dirty_since=0.0, now=10.0
    )
    assert d.should_save is False


def test_not_dirty_returns_false():
    d = should_autosave(
        is_dirty=False, auto_save_enabled=True, dirty_since=0.0, now=10.0
    )
    assert d.should_save is False


def test_no_dirty_since_returns_false():
    d = should_autosave(
        is_dirty=True, auto_save_enabled=True, dirty_since=None, now=10.0
    )
    assert d.should_save is False


def test_within_debounce_returns_false():
    d = should_autosave(
        is_dirty=True,
        auto_save_enabled=True,
        dirty_since=10.0,
        now=12.0,
        debounce_seconds=3.0,
    )
    assert d.should_save is False


def test_after_debounce_returns_true():
    d = should_autosave(
        is_dirty=True,
        auto_save_enabled=True,
        dirty_since=10.0,
        now=15.0,
        debounce_seconds=3.0,
    )
    assert d.should_save is True
    assert d.seconds_since_dirty >= 3.0
