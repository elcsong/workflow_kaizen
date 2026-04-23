"""신규 사용자 1-page 튜토리얼 — Dismissible.

Streamlit 호출은 최소화하고 결정 함수는 순수하게 분리해 테스트한다.
"""
from __future__ import annotations

ONBOARDING_TITLE = "👋 English Kaizen 사용 가이드"

ONBOARDING_BODY_MD = """
**6-Step TED 청취 학습법**으로 영어 듣기와 표현력을 끌어올리세요.

| 단계 | 핵심 행동 |
|------|----------|
| **1부 (Listening)** | Step 1-3 — 자막 OFF로 큰 흐름 파악 → 노트 → 채워넣기 |
| **2부 (Analysis)** | Step 4-6 — 자막 ON으로 직해 / 어휘·문법·연음 분석 → AI 튜터에게 질문 |
| **3부 (Shadowing)** | Step 7-10 — 오답 정리 → 섀도잉 → 녹음 → 내 말로 요약 |

### 빠른 시작
1. **➕ Start New Session** 클릭 → YouTube TED URL 붙여넣기
2. 좌측 비디오 + 우측 3개 탭 형태로 학습 화면 진입
3. AI 분석은 Phase 2 → "🤖 Ask AI to Explain" 클릭 (디폴트: 로컬 Ollama gemma4:26b)

### 팁
- 사이드바 **자동 저장 (3초)** 토글로 자동 저장 켜기
- "● Unsaved changes" 배지가 보이면 변경사항이 저장되지 않은 상태입니다
"""


def should_show_onboarding(*, dismissed: bool, session_count: int) -> bool:
    """튜토리얼 노출 여부.

    - 사용자가 이미 닫았다면 False
    - 세션이 1개 이상이면 신규 사용자 아님 → False
    - 세션 0개 + 닫지 않음 → True
    """
    if dismissed:
        return False
    return session_count == 0
