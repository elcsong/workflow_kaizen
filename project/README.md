# Intent Matcher

의료 장비 불량 유형 판별을 위한 파이썬 패키지

## 개요

Intent Matcher는 사용자가 지정한 타겟 불량 유형과 각 complaint record가 동일 불량 유형인지를 판별하는 도구입니다. 키워드 기반 룰과 SBERT 의미 분석을 결합하여 높은 정확도의 판별을 제공합니다.

## 주요 기능

- **하이브리드 분석**: 룰 기반 + SBERT 의미 분석 결합
- **증상 필수 조건**: 증상 키워드 매칭을 필수로 하는 정책 지원
- **부정 문맥 감지**: "not reproducible", "resolved" 등의 부정 패턴 자동 감지
- **증거 추출**: 판별 근거가 되는 텍스트 스팬 자동 추출
- **유연한 설정**: YAML 기반 타겟 불량 정의 및 정책 설정

## 설치

### 🎯 초보자용 가이드 (추천)
- **[🚀 초보자 완전 가이드](BEGINNER_GUIDE.md)**: 설치부터 실전 사용까지 단계별 가이드 ⭐
- **[📋 빠른 시작 스크립트](run_beginner_examples.bat)**: 클릭 한 번으로 예제 실행

### 📋 상세 설치 가이드
자세한 설치 방법은 **[MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md)** 를 참고하세요.

### ⚡ 빠른 설치 요약

**1단계: Python 환경 준비**

Windows:
```bash
# 프로젝트 디렉토리로 이동
cd C:\project

# 가상 환경 생성 및 활성화
python -m venv cvenv
cvenv\Scripts\activate
```

macOS/Linux:
```bash
# 프로젝트 디렉토리로 이동
cd /path/to/project/intent_matcher_for_test

# 가상 환경 생성 및 활성화
python3 -m venv cvenv
source cvenv/bin/activate
```

**2단계: 필수 패키지 설치**
```bash
# 기본 패키지 (필수)
pip install pandas>=1.3.0 pyyaml>=5.4.0 numpy>=1.20.0 openpyxl>=3.0.0

# SBERT 패키지 (선택사항 - 의미 분석용)
pip install sentence-transformers torch transformers
```

**3단계: 샘플 데이터 확인**
샘플 데이터는 `data/sample_complaints.xlsx`에 이미 포함되어 있습니다.
직접 생성하려면 Python 스크립트를 사용할 수 있습니다.

**4단계: 설치 테스트**
```bash
# Windows
python intent_matcher\cli\hybrid_match.py --file data\sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"

# macOS/Linux
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"
```

## 빠른 시작

⚠️ **중요**: 모듈 실행(`python -m`)에서 인수 인식 오류가 발생할 수 있습니다. 아래와 같이 직접 파일 실행을 권장합니다.

### 🎯 하이브리드 분석 (권장) - 완전한 스코어링 시스템

Windows:
```bash
# 가상 환경 활성화 (매번 사용 전에 필요)
cvenv\Scripts\activate

# 기본 하이브리드 분석 (타겟 ID + 키워드 필터링 + 완전한 분석)
python intent_matcher\cli\hybrid_match.py --file data\sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"

# SBERT 의미 분석 포함 (더 정확한 결과)
python intent_matcher\cli\hybrid_match.py --file data\sample_complaints.xlsx --target-id "COM-21912149" --keywords "blood,flow" --use-sbert
```

macOS/Linux:
```bash
# 가상 환경 활성화 (매번 사용 전에 필요)
source cvenv/bin/activate

# 기본 하이브리드 분석 (타겟 ID + 키워드 필터링 + 완전한 분석)
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"

# SBERT 의미 분석 포함 (더 정확한 결과)
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "blood,flow" --use-sbert
```

공통 옵션 예시:
```bash
# 가중치 조정 (규칙 70%, 의미 30%)
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "freeze,hang" --alpha 0.7

# 유사도 임계값 조정
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "battery,power" --threshold 0.8

# 결과 파일명 지정
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "display,screen" --output analysis_results.xlsx
```

### 🔧 키워드만 기반 분석 (단순 필터링)

Windows:
```bash
python intent_matcher\cli\keyword_match.py --file data\sample_complaints.xlsx --keywords "blood,bleed,crystal"
```

macOS/Linux:
```bash
python intent_matcher/cli/keyword_match.py --file data/sample_complaints.xlsx --keywords "blood,bleed,crystal"
```

SBERT 포함 키워드 분석:
```bash
# Windows
python intent_matcher\cli\keyword_match.py --file data\sample_complaints.xlsx --keywords "artifact,image" --use-sbert

# macOS/Linux  
python intent_matcher/cli/keyword_match.py --file data/sample_complaints.xlsx --keywords "artifact,image" --use-sbert
```

### 🎯 성능 및 정확도 비교

**SBERT 미포함 vs 포함 비교:**

⚠️ **실행 방법 주의**: 모듈 실행(`-m` 옵션)에서 문제가 발생할 수 있습니다. 직접 파일 실행을 권장합니다.

```bash
# 빠른 분석 (SBERT 미포함) - 직접 파일 실행 방식
python intent_matcher/cli/hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe"
# 결과: 평균 점수 ~0.2, 주로 Review/False 판정

# 정확한 분석 (SBERT 포함) - 권장
python intent_matcher/cli/hybrid_match.py --file data/complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe" --use-sbert
# 결과: 평균 점수 ~0.7, 더 많은 True 판정, 3배 높은 정확도
```

### 💡 사용 팁

**하이브리드 분석 최적화**
```bash
# 타겟 ID 선택 팁
- 명확한 결함 유형의 대표 사례 선택
- 충분한 텍스트 정보가 있는 레코드 선택
- 해결된 사례보다는 문제 상황이 잘 기술된 사례

# 키워드 선택 팁  
- 구체적인 키워드: "crystal" > "problem"
- 타겟과 관련된 키워드: "artifact,probe,beamformer"
- 동의어 활용: "freeze,hang,stuck"

# 임계값 조정
--threshold 0.9  # 매우 엄격한 키워드 매칭
--threshold 0.7  # 균형잡힌 매칭 (기본값)  
--threshold 0.5  # 관대한 키워드 매칭

# 분석 정확도 vs 성능
--use-sbert --alpha 0.3  # 의미 분석 중심 (느리지만 정확)
--alpha 0.7              # 규칙 기반 중심 (빠르고 해석 가능)
(기본값) --alpha 0.5     # 균형잡힌 분석
```

**가상 환경 관리**

Windows:
```bash
# 가상 환경 활성화
cvenv\Scripts\activate

# 가상 환경 비활성화
deactivate
```

macOS/Linux:
```bash
# 가상 환경 활성화
source cvenv/bin/activate

# 가상 환경 비활성화
deactivate
```

공통:
```bash
# 설치된 패키지 확인
pip list
```

**다양한 분석 예시**

Windows:
```bash
# 하이브리드 분석 (권장) - 완전한 스코어링
python intent_matcher\cli\hybrid_match.py --file data\sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact"

# 키워드 기반 분석 - 단순 필터링
python intent_matcher\cli\keyword_match.py --file data\sample_complaints.xlsx --keywords "freeze,crystal,blood"

# 하이브리드 분석 - 동적 타겟 + 완전한 스코어링 (권장)
python intent_matcher\cli\hybrid_match.py --file data\sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe" --use-sbert
```

macOS/Linux:
```bash
# 하이브리드 분석 (권장) - 완전한 스코어링
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact"

# 키워드 기반 분석 - 단순 필터링
python intent_matcher/cli/keyword_match.py --file data/sample_complaints.xlsx --keywords "freeze,crystal,blood"

# 하이브리드 분석 - 동적 타겟 + 완전한 스코어링 (권장)
python intent_matcher/cli/hybrid_match.py --file data/sample_complaints.xlsx --target-id "COM-21912149" --keywords "crystal,artifact,probe" --use-sbert
```

## 타겟 불량 정의 (YAML)

```yaml
id: DF_FREEZE_001
name: "Image freezes during scan"

symptoms:
  required_any: ["freeze", "hang", "stuck", "crash"]
  synonyms: ["lock up", "stalled", "image stuck"]

negation_patterns: 
  - "not reproducible"
  - "resolved"
  - "passed all tests"

action_hints: 
  - "reload software"
  - "upgrade"
  - "reinstall"

component_hints: 
  - "software"
  - "platform"
  - "application"

confusers: 
  - "artifact"
  - "boot failure"

policy:
  require_symptom: true
  min_score: 0.60
  review_band: [0.55, 0.60]
  treat_resolved_as_match: true
```

## 프로그래밍 인터페이스

```python
from intent_matcher import DefectMatcher

# 매처 초기화
matcher = DefectMatcher(
    target_config_path='targets/DF_FREEZE_001.yaml',
    use_sbert=True,
    alpha=0.5
)

# 단일 레코드 분석
record = {
    'Customers': 'System freezes during imaging',
    'FE': 'Confirmed freeze issue',
    'Actions': 'Restarted system, issue resolved',
    'Test': 'All tests passed after restart'
}

result = matcher.analyze_record(record)
print(f"판정: {result.same_defect}")
print(f"점수: {result.final_score}")
print(f"근거: {result.reasoning}")

# Excel 파일 분석
results_df = matcher.analyze_excel('data/complaints.xlsx')
results_df.to_csv('results.csv', index=False)
```

## 출력 결과

분석 결과는 다음 컬럼들을 포함합니다:

- `SameDefect`: 판정 결과 (True/False/Review)
- `FinalScore`: 최종 점수 (0.0~1.0)
- `Confidence`: 신뢰도 (0.0~1.0)
- `RuleScore`: 룰 기반 점수
- `SemanticScore`: 의미 분석 점수
- `Reasoning`: 판정 근거
- `Filter_Context`: 키워드가 발견된 문맥 정보 (하이브리드 분석 전용)
- `Filter_Details`: 키워드 매칭 상세 정보 (하이브리드 분석 전용)

## ⚙️ 임계값 동적 설정

**NEW!** 이제 분석 중 임계값을 동적으로 조정할 수 있습니다.

### 빠른 사용법

**CLI에서 임계값 설정**
```bash
# 더 엄격한 기준 적용
python intent_matcher/cli/hybrid_match.py \
  --file data/complaints.xlsx --target-id COM123 --keywords "error,issue" \
  --min-score 0.8 --review-band 0.7,0.8 --require-symptom false

# 관대한 기준 적용  
python intent_matcher/cli/hybrid_match.py \
  --file data/complaints.xlsx --target-id COM123 --keywords "error,issue" \
  --min-score 0.5 --review-band 0.4,0.5
```

**코드에서 임계값 설정**
```python
from intent_matcher.core.hybrid_matcher import HybridMatcher

# 인스턴스 생성 시 설정
matcher = HybridMatcher(
    excel_path="data.xlsx",
    target_complaint_id="COM123", 
    filter_keywords="error,issue",
    min_score=0.7,              # 임계값 설정
    review_band=(0.6, 0.7),     # 리뷰 구간
    require_symptom=False       # 증상 필수 여부
)

# 분석 실행 시 오버라이드
result_df, summary = matcher.analyze_excel(
    min_score=0.8,              # 더 높은 임계값 적용
    require_symptom=True        # 증상 필수로 변경
)
```

### 주요 임계값 옵션

| 옵션 | 기본값 | 설명 | 예시 |
|------|--------|------|------|
| `min_score` | 0.6 | 최소 임계점 (이상이면 True) | `0.8` (엄격) / `0.5` (관대) |
| `review_band` | (0.55, 0.60) | 리뷰 구간 (Human review) | `(0.7, 0.8)` |
| `require_symptom` | True | 증상 키워드 필수 여부 | `False` (선택적) |
| `alpha` | 0.5 | 룰 vs 의미 점수 가중치 | `0.7` (룰 중심) |

### 실전 예시

```bash
# 시나리오 1: 고품질 매칭만 원하는 경우
--min-score 0.85 --review-band 0.8,0.85 --require-symptom true

# 시나리오 2: 더 많은 후보를 찾고 싶은 경우  
--min-score 0.5 --review-band 0.4,0.5 --require-symptom false

# 시나리오 3: 룰 기반 분석 중심 (빠른 분석)
--alpha 0.8 --min-score 0.7

# 시나리오 4: 의미 분석 중심 (정확한 분석)
--alpha 0.3 --min-score 0.6 --use-sbert
```

**📖 상세 가이드**: [THRESHOLD_CONFIGURATION.md](THRESHOLD_CONFIGURATION.md)에서 모든 설정 방법과 고급 기능을 확인하세요.

## 📁 프로젝트 구조

```
project/

├─ intent_matcher/
│   ├─ cli/
│   │   ├─ hybrid_match.py           # 하이브리드 실행 CLI
│   │   ├─ keyword_match.py
│   │   └─ match.py                  # 정적 타깃 실행 CLI
│   ├─ config/
│   │   └─ nlp_config.yaml           # Stopwords/Allowlist
│   ├─ core/
│   │   ├─ hybrid_matcher.py
│   │   ├─ keyword_matcher.py
│   │   └─ matcher.py
│   ├─ extract/
│   │   ├─ keywords.py
│   │   └─ negation.py
│   ├─ notes/
│   │   └─ Runbook.md                # Obsidian용 실행 가이드
│   ├─ scoring/
│   │   ├─ combine.py
│   │   ├─ policy.py                 # 필드 가중치 정책
│   │   └─ rules.py                  # 규칙 점수 계산
│   └─ semantics/
│       ├─ finetune.py
│       └─ sbert.py                  # SBERT 의미 분석
├─ last_test.xlsx
├─ models/
│   └─ all-MiniLM-L6-v2              # SBERT 로컬 모델
├─ requirements.txt
├─ setup.py
├─ targets/
│   └─ DYNAMIC_COM-27127917.yaml     # 정적 타깃 YAML
└─ 해설_GUIDE.md                     # 리포트 필드 해설
```

## 🚀 확장 계획

- [ ] SBERT 파인튜닝 기능 활성화
- [ ] 구조화 코드 (SPCR/SPC) 매칭 구현
- [ ] 다중 불량 유형 지원
- [ ] 웹 인터페이스 추가
- [ ] 평가 및 검증 도구 개선
- [ ] 배치 처리 기능 강화
- [ ] GUI 버전 개발

## 🔧 문제 해결

설치나 사용 중 문제가 발생하면:

1. 가상 환경이 활성화되었는지 확인:
   - Windows: `cvenv\Scripts\activate`
   - macOS/Linux: `source cvenv/bin/activate`
2. 패키지가 올바르게 설치되었는지 확인: `pip list`
3. Python 버전 확인: `python --version` 또는 `python3 --version` (3.8 이상 필요)
4. requirements.txt를 사용하여 패키지 설치: `pip install -r requirements.txt`

## 📄 라이선스

MIT License

## 📞 문의

- 설치 관련: **MANUAL_SETUP_GUIDE.md** 참고
- 사용법 관련: CLI 명령어 `--help` 옵션 사용
- 개발 관련: GitHub 이슈 등록

---

**Intent Matcher v0.1.0** - 의료기기 결함 분류를 위한 하이브리드 분석 도구
