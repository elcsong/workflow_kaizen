# 임계값 동적 설정 가이드 (Threshold Configuration Guide)

Intent Matcher 시스템에서 분석 결과의 True/False 판별을 위한 임계값을 동적으로 설정하는 방법에 대한 상세 가이드입니다.

## 목차

1. [개요](#개요)
2. [임계값 종류](#임계값-종류)
3. [설정 방법](#설정-방법)
4. [우선순위](#우선순위)
5. [사용 예시](#사용-예시)
6. [고급 설정](#고급-설정)
7. [문제 해결](#문제-해결)

## 개요

기존에는 임계값이 코드에 하드코딩되어 있어 변경이 어려웠지만, 이제 다음과 같은 방법으로 동적으로 설정할 수 있습니다:

- **CLI 매개변수**: 명령행에서 직접 지정
- **메서드 매개변수**: 코드에서 메서드 호출 시 지정  
- **실시간 변경**: 분석 중간에 설정 변경
- **설정 파일**: YAML 파일에서 기본값 설정

## 임계값 종류

### 1. min_score (최소 임계점)
- **기본값**: 0.6
- **범위**: 0.0 ~ 1.0
- **설명**: 이 값 이상이면 'True'로 판별
- **예시**: 0.7로 설정하면 점수 0.7 이상일 때만 'True'

### 2. review_band (리뷰 구간)
- **기본값**: (0.55, 0.60)
- **형식**: (하한, 상한) 튜플
- **설명**: 이 구간 내 점수는 'Review'로 판별
- **예시**: (0.5, 0.7)로 설정하면 0.5~0.7 사이는 인간 검토 필요

### 3. require_symptom (증상 필수 여부)
- **기본값**: True
- **타입**: Boolean
- **설명**: 증상 키워드가 반드시 발견되어야 하는지 여부
- **예시**: False로 설정하면 증상 없어도 다른 조건으로 'True' 가능

### 4. treat_resolved_as_match (해결된 케이스 매칭)
- **기본값**: True  
- **타입**: Boolean
- **설명**: "resolved", "fixed" 등의 해결 표현을 매칭으로 인정할지 여부
- **예시**: False로 설정하면 해결된 케이스는 매칭에서 제외

### 5. alpha (룰 vs 의미 점수 가중치)
- **기본값**: 0.5
- **범위**: 0.0 ~ 1.0
- **설명**: 룰 기반 점수의 가중치 (1-alpha는 의미 점수 가중치)
- **예시**: 0.7로 설정하면 룰 점수 70%, 의미 점수 30% 반영

## 설정 방법

### 1. CLI 매개변수 방식

#### HybridMatcher 사용 시
```bash
# 기본 사용
python -m intent_matcher.core.hybrid_matcher \
  --file data.xlsx --target-id COM123 --keywords "error,issue" \
  --min-score 0.7 --review-band 0.6,0.7 --require-symptom false

# 모든 임계값 설정
python -m intent_matcher.core.hybrid_matcher \
  --file data.xlsx --target-id COM123 --keywords "error,issue" \
  --min-score 0.75 \
  --review-band 0.65,0.75 \
  --require-symptom true \
  --treat-resolved-as-match false \
  --alpha 0.6
```

#### DefectMatcher 사용 시
```bash
# target_config.yaml과 함께 사용
python your_analysis.py \
  --min-score 0.8 \
  --review-band 0.7,0.8 \
  --require-symptom false
```

### 2. 메서드 매개변수 방식

#### HybridMatcher
```python
from intent_matcher.core.hybrid_matcher import HybridMatcher

# 인스턴스 생성 시 설정
matcher = HybridMatcher(
    excel_path="data.xlsx",
    target_complaint_id="COM123",
    filter_keywords="error,issue",
    min_score=0.7,                    # 임계값 설정
    review_band=(0.6, 0.7),          # 리뷰 구간 설정
    require_symptom=False,           # 증상 필수 여부
    treat_resolved_as_match=True     # 해결된 케이스 매칭 여부
)

# 분석 실행 시 설정 (인스턴스 설정 오버라이드)
result_df, summary = matcher.analyze_excel(
    min_score=0.8,                   # 더 높은 임계값 적용
    review_band=(0.7, 0.8),         # 다른 리뷰 구간 적용
)
```

#### DefectMatcher
```python
from intent_matcher.core.matcher import DefectMatcher

# 인스턴스 생성 시 설정
matcher = DefectMatcher(
    target_config_path="config.yaml",
    min_score=0.75,
    review_band=(0.65, 0.75),
    require_symptom=True
)

# 데이터프레임 분석 시 설정
result_df = matcher.analyze_dataframe(
    df=data_df,
    text_columns=["Customers", "FE", "Actions", "Test"],
    min_score=0.8,                   # 메서드 레벨 오버라이드
    require_symptom=False            # 임시로 증상 필수 해제
)
```

### 3. 실시간 설정 변경

#### ScoreCombiner 직접 제어
```python
# 분석 중간에 임계값 변경
matcher.score_combiner.update_thresholds(
    min_score=0.8,
    review_band=(0.7, 0.8),
    require_symptom=False
)

# 현재 설정 확인
current_settings = matcher.score_combiner.get_current_settings()
print(current_settings)

# 기본값으로 리셋
matcher.score_combiner.reset_thresholds()
```

#### PolicyManager 사용
```python
# 정책 매니저를 통한 일괄 변경
policy_updates = {
    'min_score': 0.75,
    'review_band': (0.65, 0.75),
    'require_symptom': False,
    'alpha': 0.7
}

matcher.policy_manager.batch_update(policy_updates)

# 개별 설정 변경
matcher.policy_manager.update_thresholds(
    min_score=0.8,
    require_symptom=True
)
```

### 4. 설정 파일 방식

#### YAML 설정 파일 (target_config.yaml)
```yaml
id: "DEFECT_001"
name: "Display Issue Detection"

# 기본 임계값 설정
policy:
  require_symptom: true
  min_score: 0.65               # 기본 임계값
  review_band: [0.55, 0.65]     # 기본 리뷰 구간  
  treat_resolved_as_match: true
  alpha: 0.5                    # 룰 vs 의미 점수 가중치

symptoms:
  required_any: ["display", "screen", "monitor"]
  synonyms: ["lcd", "led", "panel"]
```

#### 동적 설정 로드
```python
# 설정 파일에서 로드 후 CLI 인수로 오버라이드
matcher = DefectMatcher("config.yaml")

# CLI 인수 딕셔너리 적용
cli_args = {
    'min_score': 0.8,
    'review_band': (0.7, 0.8),
    'require_symptom': False
}
matcher.policy_manager.load_from_cli_args(cli_args)
```

## 우선순위

임계값 설정의 우선순위는 다음과 같습니다 (높은 순서부터):

1. **메서드 매개변수** - `analyze_excel()`, `analyze_dataframe()` 호출 시 전달
2. **CLI 매개변수** - 명령행에서 `--min-score` 등으로 지정
3. **인스턴스 설정** - 객체 생성 시 전달된 매개변수
4. **설정 파일** - YAML 파일의 policy 섹션
5. **기본값** - 코드에 하드코딩된 기본값

### 우선순위 예시
```python
# 1. 설정 파일: min_score = 0.6
# 2. 인스턴스 생성: min_score = 0.7  
# 3. 메서드 호출: min_score = 0.8

matcher = DefectMatcher("config.yaml", min_score=0.7)  # 0.6 → 0.7로 오버라이드
result = matcher.analyze_dataframe(df, columns, min_score=0.8)  # 0.7 → 0.8로 오버라이드

# 최종 사용되는 min_score = 0.8
```

## 사용 예시

### 시나리오 1: 엄격한 판별 기준
고품질 매칭만 원하는 경우:
```python
matcher = HybridMatcher(
    excel_path="data.xlsx",
    target_complaint_id="COM123",
    filter_keywords="critical,severe",
    min_score=0.85,              # 높은 임계값
    review_band=(0.8, 0.85),     # 좁은 리뷰 구간
    require_symptom=True,        # 증상 필수
    alpha=0.7                    # 룰 기반 점수 중시
)
```

### 시나리오 2: 관대한 판별 기준  
더 많은 매칭을 찾고 싶은 경우:
```python
matcher = HybridMatcher(
    excel_path="data.xlsx", 
    target_complaint_id="COM123",
    filter_keywords="issue,problem",
    min_score=0.5,               # 낮은 임계값
    review_band=(0.4, 0.5),      # 넓은 리뷰 구간
    require_symptom=False,       # 증상 선택적
    alpha=0.3                    # 의미 점수 중시
)
```

### 시나리오 3: 실험적 임계값 탐색
최적 임계값을 찾기 위한 실험:
```python
# 여러 임계값으로 실험
thresholds_to_test = [0.5, 0.6, 0.7, 0.8]

for threshold in thresholds_to_test:
    result_df, summary = matcher.analyze_excel(
        min_score=threshold,
        output_path=f"results_threshold_{threshold}.xlsx"
    )
    
    print(f"Threshold {threshold}: {summary['same_defect_true']} matches found")
```

### 시나리오 4: 단계별 분석
점진적으로 임계값을 조정하면서 분석:
```python
# 1단계: 관대한 기준으로 후보 찾기
candidates_df, _ = matcher.analyze_excel(min_score=0.5)

# 2단계: 엄격한 기준으로 확정
final_df, _ = matcher.analyze_excel(
    min_score=0.8,
    require_symptom=True,
    output_path="final_results.xlsx"
)
```

## 고급 설정

### 1. 동적 임계값 조정
분석 결과에 따라 임계값을 동적으로 조정:

```python
def adaptive_analysis(matcher, df):
    """적응형 임계값 분석"""
    
    # 초기 분석 (관대한 기준)
    initial_results, summary = matcher.analyze_excel(min_score=0.5)
    
    # 결과에 따라 임계값 조정
    true_count = summary.get('same_defect_true', 0)
    
    if true_count > 100:  # 너무 많은 매칭
        adjusted_threshold = 0.75
    elif true_count < 10:  # 너무 적은 매칭  
        adjusted_threshold = 0.45
    else:
        adjusted_threshold = 0.6
    
    # 조정된 임계값으로 재분석
    final_results, _ = matcher.analyze_excel(
        min_score=adjusted_threshold,
        output_path=f"adaptive_results_threshold_{adjusted_threshold}.xlsx"
    )
    
    return final_results, adjusted_threshold
```

### 2. 임계값 최적화
그리드 서치를 통한 최적 임계값 탐색:

```python
def optimize_thresholds(matcher, validation_data):
    """임계값 최적화 (그리드 서치)"""
    
    best_score = 0
    best_params = {}
    
    # 파라미터 그리드 정의
    min_scores = [0.5, 0.6, 0.7, 0.8]
    alphas = [0.3, 0.5, 0.7]
    require_symptoms = [True, False]
    
    for min_score in min_scores:
        for alpha in alphas:
            for require_symptom in require_symptoms:
                # 임계값 적용하여 분석
                results, summary = matcher.analyze_excel(
                    min_score=min_score,
                    require_symptom=require_symptom,
                    alpha=alpha
                )
                
                # 성능 평가 (F1 스코어 등)
                score = evaluate_performance(results, validation_data)
                
                if score > best_score:
                    best_score = score
                    best_params = {
                        'min_score': min_score,
                        'alpha': alpha,
                        'require_symptom': require_symptom
                    }
    
    return best_params, best_score
```

### 3. 조건부 임계값 설정
데이터 특성에 따른 조건부 임계값:

```python
def conditional_thresholds(matcher, df):
    """데이터 특성에 따른 조건부 임계값"""
    
    results = []
    
    for idx, row in df.iterrows():
        # 텍스트 길이에 따른 임계값 조정
        text_length = len(str(row['Customers Issue Description(Full)']))
        
        if text_length < 100:  # 짧은 텍스트
            threshold = 0.5
            review_band = (0.4, 0.5)
        elif text_length > 500:  # 긴 텍스트
            threshold = 0.7
            review_band = (0.6, 0.7)
        else:  # 보통 텍스트
            threshold = 0.6
            review_band = (0.55, 0.6)
        
        # 개별 레코드 분석
        record = {
            'Customers': str(row['Customers Issue Description(Full)']),
            'FE': str(row["FE's Issue Description(Full)"]),
            'Actions': str(row['Actions Taken / Repairs(Full)']),
            'Test': str(row['Repair Test / Inspection Data(Full)'])
        }
        
        result = matcher.analyze_record(
            record,
            min_score=threshold,
            review_band=review_band
        )
        
        results.append(result)
    
    return results
```

## 문제 해결

### 1. 임계값 설정이 적용되지 않는 경우

**증상**: 설정한 임계값이 무시되는 것 같음

**해결방법**:
```python
# 현재 설정 확인
current_settings = matcher.score_combiner.get_current_settings()
print("현재 임계값 설정:", current_settings)

# 우선순위 확인
print("우선순위별 설정:")
print("1. 메서드 매개변수:", locals().get('min_score'))
print("2. 인스턴스 설정:", matcher.threshold_overrides)
print("3. 기본값:", matcher.score_combiner._default_min_score)
```

### 2. 리뷰 구간 설정 오류

**증상**: `ValueError: review_band must be (lower, upper) with lower < upper`

**해결방법**:
```python
# 올바른 형식
review_band = (0.55, 0.60)  # OK: 하한 < 상한

# 잘못된 형식들
review_band = (0.60, 0.55)  # 에러: 하한 >= 상한
review_band = [0.55, 0.60]  # 경고: 리스트는 자동으로 튜플 변환됨
```

### 3. CLI 매개변수 파싱 오류

**증상**: `--review-band` 옵션에서 파싱 에러

**해결방법**:
```bash
# 올바른 형식
--review-band 0.55,0.60

# 잘못된 형식들
--review-band "0.55, 0.60"  # 공백 포함
--review-band 0.55-0.60     # 다른 구분자
```

### 4. 임계값 범위 오류

**증상**: `ValueError: min_score must be between 0.0 and 1.0`

**해결방법**:
```python
# 올바른 범위
min_score = 0.75    # OK: 0.0 ~ 1.0
alpha = 0.6         # OK: 0.0 ~ 1.0

# 잘못된 범위
min_score = 1.5     # 에러: > 1.0
alpha = -0.1        # 에러: < 0.0
```

### 5. 성능 문제

**증상**: 임계값 설정 후 분석 속도 저하

**해결방법**:
```python
# SBERT 비활성화로 속도 향상
matcher = HybridMatcher(
    excel_path="data.xlsx",
    target_complaint_id="COM123", 
    filter_keywords="issue",
    use_sbert=False,          # SBERT 비활성화
    alpha=1.0                 # 룰 점수만 사용
)

# 또는 룰 기반 점수 위주로 설정
matcher = HybridMatcher(
    excel_path="data.xlsx",
    target_complaint_id="COM123",
    filter_keywords="issue", 
    alpha=0.9                 # 룰 점수 90%, 의미 점수 10%
)
```

### 6. 디버깅 정보 활성화

임계값 설정 관련 상세 로그 확인:
```python
import logging

# 디버그 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# 분석 실행 (상세 로그 출력됨)
result_df, summary = matcher.analyze_excel(min_score=0.7)

# 설정 상태 덤프
print("=== 임계값 설정 상태 ===")
print(matcher.policy_manager.get_current_config_summary())
```

## 관련 문서

- [README.md](README.md) - 전체 시스템 개요
- [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md) - 초보자 가이드  
- [MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md) - 수동 설치 가이드

---

이 가이드가 도움이 되었다면, 실제 사용 사례나 추가 질문이 있으시면 언제든 문의해 주세요.
