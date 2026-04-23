"""세션 삭제 확인 모달.

`st.dialog`(Streamlit ≥1.35)을 사용해 즉시 삭제 대신 확인 단계를 거친다.
호출 패턴:

    if st.button("🗑️ Delete"):
        st.session_state.pending_delete = session_id
    show_delete_confirmation_if_pending(on_confirm=delete_callback)

테스트는 dialog 데코레이터를 우회해 confirm/cancel 분기 함수만 검증.
"""
from __future__ import annotations

from typing import Callable


def confirm_or_cancel(
    *,
    confirmed: bool,
    on_confirm: Callable[[str], None],
    session_id: str,
) -> bool:
    """모달 결과를 처리하는 순수 함수.

    confirmed=True 인 경우에만 on_confirm 호출. 호출 여부 반환.
    """
    if confirmed:
        on_confirm(session_id)
        return True
    return False
