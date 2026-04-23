"""온보딩 노출 결정 함수 검증."""
from __future__ import annotations

from english_app.ui.components.onboarding import should_show_onboarding


def test_show_for_brand_new_user():
    assert should_show_onboarding(dismissed=False, session_count=0) is True


def test_hide_when_user_dismissed():
    assert should_show_onboarding(dismissed=True, session_count=0) is False


def test_hide_when_user_already_has_sessions():
    assert should_show_onboarding(dismissed=False, session_count=3) is False


def test_dismissed_overrides_session_count_zero():
    assert should_show_onboarding(dismissed=True, session_count=0) is False
