# 📚 키워드 매칭 및 Rule Score 계산 가이드

> **대상 독자**: 프로그래밍 초보자, 코드베이스를 처음 접하는 개발자  
> **목적**: `--keywords`로 입력한 키워드가 어떻게 매칭되고 Rule Score가 계산되는지 완전히 이해하기

---

## 📋 목차

1. [전체 흐름 개요](#1-전체-흐름-개요)
2. [단계 1: 키워드 입력 및 파싱](#2-단계-1-키워드-입력-및-파싱)
3. [단계 2: Seeds 생성 (키워드 확장)](#3-단계-2-seeds-생성-키워드-확장)
4. [단계 3: KeywordExtractor 패턴 생성](#4-단계-3-keywordextractor-패턴-생성)
5. [단계 4: 텍스트에서 키워드 매칭](#5-단계-4-텍스트에서-키워드-매칭)
6. [단계 5: Rule Score 계산](#6-단계-5-rule-score-계산)
7. [단계 6: 최종 판정](#7-단계-6-최종-판정)
8. [실전 예제](#8-실전-예제)
9. [FAQ](#9-faq)

---

## 1. 전체 흐름 개요

```
사용자 입력: --keywords "femur, femur length, out of range"
    ↓
[1단계] 키워드 파싱: 콤마로 분리
    ↓
[2단계] Seeds 생성: 구문 보존 + 개별 단어 추가
    ↓
[3단계] 패턴 생성: 정규식 패턴으로 변환
    ↓
[4단계] 텍스트 매칭: 실제 텍스트에서 키워드 찾기
    ↓
[5단계] Rule Score 계산: 찾은 키워드 개수로 점수 산정
    ↓
[6단계] 최종 판정: True/False/Review 결정
```

---

## 2. 단계 1: 키워드 입력 및 파싱

### 입력 예시
```bash
--keywords "femur, femur length, out of range"
```

### 처리 과정

**코드 위치**: `hybrid_matcher.py` → `_parse_keywords()` 메서드

```python
# 입력 문자열을 콤마(,)로 분리
입력: "femur, femur length, out of range"
↓
파싱 결과: ['femur', 'femur length', 'out of range']
```

### 📝 규칙

1. **콤마(,)로 구분**: 각 키워드는 콤마로 분리됩니다
2. **공백 제거**: 앞뒤 공백은 자동으로 제거됩니다
3. **대소문자 변환**: 모든 키워드는 소문자로 변환됩니다
4. **따옴표 보호**: 따옴표로 묶인 구문은 하나의 키워드로 유지됩니다
   - 예: `"femur length"` → `['femur length']` (분리 안 됨)

### 예시

| 입력 | 파싱 결과 |
|------|----------|
| `"femur, length"` | `['femur', 'length']` |
| `"femur, femur length"` | `['femur', 'femur length']` |
| `'"femur length", mirror'` | `['femur length', 'mirror']` |

---

## 3. 단계 2: Seeds 생성 (키워드 확장)

### ⚠️ 중요: Seeds는 무엇인가?

**Seeds**는 `--keywords`로 입력한 키워드들을 **처리 및 확장한 결과**입니다.

- ✅ **토큰화된 키워드** 포함 (예: `"double-clicking"` → `["double", "clicking"]`)
- ✅ **구문 키워드** 그대로 포함 (예: `"femur length"` → `["femur length"]`)
- ✅ **개별 단어** 추가 (예: `"femur length"` → `["femur length", "femur", "length"]`)
- ✅ **와일드카드** 그대로 보존 (예: `"duplicat*"` → `["duplicat*"]`)

**즉, Seeds = 처리 및 확장된 키워드 집합** (단순히 토큰화만이 아님!)

### 목적
- 구문 키워드는 그대로 유지
- 개별 단어도 추가하여 유연한 매칭 지원

**코드 위치**: `hybrid_matcher.py` → `DynamicTargetConfig._build_config()` → Seeds 생성 부분 (124번 라인 주석: "씨앗(Seeds) 구성")

### 처리 과정

```python
입력: ['femur', 'femur length', 'out of range']
↓
Seeds 생성:
  1. 'femur' → 단일 단어 → 그대로 추가
  2. 'femur length' → 구문 → 전체 + 개별 단어 분리
     - 'femur length' (구문 전체)
     - 'femur' (이미 있음, 중복 제거)
     - 'length' (개별 단어 추가)
  3. 'out of range' → 구문 → 전체 + 개별 단어 분리
     - 'out of range' (구문 전체)
     - 'out' (stopwords 제외 가능)
     - 'of' (stopwords 제외)
     - 'range' (개별 단어 추가)
↓
최종 Seeds: ['femur', 'femur length', 'length', 'out of range', 'range']
```

### 📝 규칙

#### 1. 단일 단어 키워드
- 그대로 추가
- 예: `'femur'` → `['femur']`

#### 2. 구문 키워드 (공백 포함)
- 구문 전체를 추가
- 개별 단어도 각각 추가
- 예: `'femur length'` → `['femur length', 'femur', 'length']`

#### 3. 와일드카드 키워드 (`*` 포함)
- 그대로 보존
- 예: `'duplicat*'` → `['duplicat*']`

#### 4. Stopwords 제거
- 일반적인 단어 (the, of, and 등)는 제외
- 예: `'out of range'`에서 `'of'`는 제외될 수 있음

### 시각적 예시

```
입력: "femur, femur length, out of range"
         ↓
    [파싱]
         ↓
['femur', 'femur length', 'out of range']
         ↓
    [Seeds 생성]
         ↓
┌─────────────────────────────────────┐
│ 'femur'          → 'femur'          │
│ 'femur length'   → 'femur length'   │
│                  → 'length'         │
│ 'out of range'   → 'out of range'   │
│                  → 'range'          │
│                  (of는 stopwords)    │
└─────────────────────────────────────┘
         ↓
최종 Seeds: ['femur', 'femur length', 'length', 'out of range', 'range']
```

---

## 4. 단계 3: KeywordExtractor 패턴 생성

### 목적
- Seeds를 정규식 패턴으로 변환하여 텍스트 검색 준비

**코드 위치**: `keywords.py` → `KeywordExtractor._create_pattern()` 메서드

### 처리 과정

```python
Seeds: ['femur', 'femur length', 'length', 'out of range', 'range']
↓
1. 길이 순 정렬 (긴 것부터 우선)
   → ['femur length', 'out of range', 'length', 'femur', 'range']
↓
2. 각 키워드를 정규식 패턴으로 변환
   - 'femur length' → 'femur\s+length' (구문)
   - 'out of range' → 'out\s+of\s+range' (구문)
   - 'length' → 'length(?:s|es|ed|ing|d)?' (어간 변화)
   - 'femur' → 'femur(?:s|es|ed|ing|d)?' (어간 변화)
   - 'range' → 'range(?:s|es|ed|ing|d)?' (어간 변화)
↓
3. 최종 패턴 생성
   → \b(?:femur\s+length|out\s+of\s+range|length(?:s|es|ed|ing|d)?|femur(?:s|es|ed|ing|d)?|range(?:s|es|ed|ing|d)?)\b
```

### 📝 패턴 타입

#### 1. 구문 패턴 (공백 포함)
```
입력: 'femur length'
패턴: 'femur\s+length'
의미: "femur"와 "length" 사이에 공백이 있는 경우 매칭
```

#### 2. 단일 단어 패턴 (어간 변화 지원)
```
입력: 'mirror'
패턴: 'mirror(?:s|es|ed|ing|d)?'
의미: mirror, mirrors, mirrored, mirroring 등 매칭
```

#### 3. 와일드카드 패턴
```
입력: 'duplicat*'
패턴: 'duplicat\w*'
의미: duplicate, duplicates, duplication 등 매칭
```

### 시각적 예시

```
Seeds: ['femur', 'femur length', 'length', 'out of range', 'range']
         ↓
    [정렬: 긴 것부터]
         ↓
['femur length', 'out of range', 'length', 'femur', 'range']
         ↓
    [패턴 변환]
         ↓
┌─────────────────────────────────────────────┐
│ 'femur length'   → femur\s+length           │
│ 'out of range'   → out\s+of\s+range         │
│ 'length'         → length(?:s|es|ed|ing|d)?│
│ 'femur'          → femur(?:s|es|ed|ing|d)? │
│ 'range'           → range(?:s|es|ed|ing|d)?│
└─────────────────────────────────────────────┘
         ↓
최종 정규식 패턴 생성 완료
```

---

## 5. 단계 4: 텍스트에서 키워드 매칭

### 목적
- 실제 텍스트에서 생성된 패턴으로 키워드 찾기

**코드 위치**: `keywords.py` → `KeywordExtractor.extract_from_text()` 메서드

### 처리 과정

```python
텍스트: "The femur length is out of range"
패턴: \b(?:femur\s+length|out\s+of\s+range|length(?:s|es|ed|ing|d)?|femur(?:s|es|ed|ing|d)?|range(?:s|es|ed|ing|d)?)\b
↓
매칭 결과:
  1. 'femur length' (위치: 4-16)
  2. 'out of range' (위치: 20-32)
```

### 📝 매칭 규칙

#### 1. 구문 우선 매칭
- 긴 구문이 먼저 매칭됩니다
- 예: `"femur length"`가 `"femur"`보다 우선

#### 2. 어간 변화 자동 매칭
- 단어의 변형 형태도 자동으로 찾습니다
- 예: `mirror` → `mirrors`, `mirrored`, `mirroring` 모두 매칭

#### 3. 대소문자 무시
- 대소문자 구분 없이 매칭됩니다
- 예: `Mirror` = `mirror` = `MIRROR`

### 예시

| 텍스트 | 키워드 | 매칭 결과 |
|--------|--------|----------|
| `"The femur length is abnormal"` | `['femur', 'femur length']` | ✅ `femur length` |
| `"Patient has short femur"` | `['femur']` | ✅ `femur` |
| `"Femur lengths are normal"` | `['femur', 'length']` | ✅ `Femur`, `lengths` |
| `"Measurement out of range"` | `['out of range', 'range']` | ✅ `range` |

---

## 6. 단계 5: Rule Score 계산

### 목적
- 찾은 키워드 개수와 위치에 따라 점수 산정

**코드 위치**: `scoring/rules.py` → `RuleScorer.calculate_symptom_score()` 메서드

### 점수 구성 요소

```
Rule Score = Symptom Score + Component Score - Negation Penalty
```

### Symptom Score 계산

#### 기본 공식

```python
base_score = 0.6  # 기본 점수
bonus_score = min(찾은_키워드_개수 - 1, 3) * 0.2  # 추가 보너스
field_weighted_score = 필드별_가중치_합산

symptom_score = min(1.0, base_score + bonus_score + field_weighted_score)
```

#### 필드별 가중치

| 필드 | 가중치 | 설명 |
|------|--------|------|
| Customers | 0.45 | 고객 설명 (가장 중요) |
| FE | 0.45 | FE 설명 (가장 중요) |
| Actions | 0.05 | 조치 내용 |
| Test | 0.05 | 테스트 결과 |

#### 계산 예시

**케이스 1: 키워드 1개 찾음**
```
텍스트: "Patient has short femur"
찾은 키워드: ['femur'] (1개)

base_score = 0.6
bonus_score = min(1-1, 3) * 0.2 = 0 * 0.2 = 0.0
field_weighted_score = 0.45 * 0.3 = 0.135 (Customers 필드)

symptom_score = min(1.0, 0.6 + 0.0 + 0.135) = 0.735
```

**케이스 2: 키워드 2개 찾음**
```
텍스트: "The femur length is out of range"
찾은 키워드: ['femur length', 'out of range'] (2개)

base_score = 0.6
bonus_score = min(2-1, 3) * 0.2 = 1 * 0.2 = 0.2
field_weighted_score = 0.45 * 0.6 = 0.27 (Customers 필드)

symptom_score = min(1.0, 0.6 + 0.2 + 0.27) = 1.0
```

**케이스 3: 키워드 3개 찾음**
```
텍스트: "Femur lengths are out of normal range"
찾은 키워드: ['femur', 'lengths', 'range'] (3개)

base_score = 0.6
bonus_score = min(3-1, 3) * 0.2 = 2 * 0.2 = 0.4
field_weighted_score = 0.45 * 0.9 = 0.405

symptom_score = min(1.0, 0.6 + 0.4 + 0.405) = 1.0
```

### 시각적 예시

```
텍스트: "The femur length is out of range"
         ↓
    [키워드 매칭]
         ↓
찾은 키워드: ['femur length', 'out of range']
         ↓
    [점수 계산]
         ↓
┌─────────────────────────────────────┐
│ base_score = 0.6                    │
│ bonus_score = (2-1) * 0.2 = 0.2     │
│ field_score = 0.45 * 0.6 = 0.27    │
│                                     │
│ symptom_score = 0.6 + 0.2 + 0.27   │
│                = 1.0 (최대값)       │
└─────────────────────────────────────┘
```

### Component Score 계산

```python
component_score = 찾은_부품_키워드_개수 * 0.1
최대값: 0.6 (6개 이상)
```

### Negation Penalty 계산

```python
# 부정 패턴 발견 시 점수 감소
negation_penalty = 0.0 ~ 0.1 (10% 감소)
```

---

## 7. 단계 6: 최종 판정

### 목적
- Rule Score와 Semantic Score를 결합하여 최종 판정

**코드 위치**: `scoring/combine.py` → `ScoreCombiner.combine_scores()` 메서드

### 점수 결합

```python
final_score = alpha * rule_score + (1 - alpha) * semantic_score

기본값: alpha = 0.5
→ final_score = 0.5 * rule_score + 0.5 * semantic_score
```

### 판정 기준

```python
if final_score >= min_score:
    return 'True'  # 동일 유형
elif final_score >= review_band[0]:
    return 'Review'  # 검토 필요
else:
    return 'False'  # 다른 유형
```

### 예시

**케이스 1: 높은 점수**
```
rule_score = 0.98
semantic_score = 0.85
alpha = 0.5

final_score = 0.5 * 0.98 + 0.5 * 0.85 = 0.915
min_score = 0.65

판정: True ✅ (0.915 >= 0.65)
```

**케이스 2: 중간 점수**
```
rule_score = 0.55
semantic_score = 0.60
alpha = 0.5

final_score = 0.5 * 0.55 + 0.5 * 0.60 = 0.575
review_band = (0.6, 0.65)

판정: False ❌ (0.575 < 0.6)
```

**케이스 3: 경계 점수**
```
rule_score = 0.62
semantic_score = 0.58
alpha = 0.5

final_score = 0.5 * 0.62 + 0.5 * 0.58 = 0.60
review_band = (0.6, 0.65)

판정: Review ⚠️ (0.60 >= 0.6 and 0.60 < 0.65)
```

---

## 8. 실전 예제

### 예제 1: 기본 케이스

**입력**
```bash
--keywords "femur, femur length, out of range"
```

**텍스트**
```
"The femur length measurement is out of range"
```

**처리 과정**

1. **파싱**: `['femur', 'femur length', 'out of range']`
2. **Seeds**: `['femur', 'femur length', 'length', 'out of range', 'range']`
3. **매칭**: `['femur length', 'out of range']` (2개)
4. **점수 계산**:
   ```
   base_score = 0.6
   bonus_score = (2-1) * 0.2 = 0.2
   field_score = 0.45 * 0.6 = 0.27
   symptom_score = 0.6 + 0.2 + 0.27 = 1.0
   ```
5. **최종 판정**: `True` (높은 점수)

### 예제 2: 어간 변화 케이스

**입력**
```bash
--keywords "mirror"
```

**텍스트**
```
"Screen shows mirrored display"
```

**처리 과정**

1. **파싱**: `['mirror']`
2. **Seeds**: `['mirror']`
3. **패턴**: `mirror(?:s|es|ed|ing|d)?`
4. **매칭**: `['mirrored']` ✅ (어간 변화 자동 매칭)
5. **점수 계산**:
   ```
   base_score = 0.6
   bonus_score = 0.0
   field_score = 0.45 * 0.3 = 0.135
   symptom_score = 0.6 + 0.0 + 0.135 = 0.735
   ```
6. **최종 판정**: `True` (0.735 >= 0.65)

### 예제 3: 와일드카드 케이스

**입력**
```bash
--keywords "duplicat*"
```

**텍스트**
```
"Image duplication detected"
```

**처리 과정**

1. **파싱**: `['duplicat*']`
2. **Seeds**: `['duplicat*']`
3. **패턴**: `duplicat\w*`
4. **매칭**: `['duplication']` ✅ (와일드카드 매칭)
5. **점수 계산**: `symptom_score = 0.735`
6. **최종 판정**: `True`

---

## 9. FAQ

### Q1: 왜 구문 키워드가 개별 단어로도 추가되나요?

**A**: 유연한 매칭을 위해입니다.
- 구문 전체가 없어도 개별 단어로 매칭 가능
- 예: `"femur length"`가 없어도 `"femur"`만 있어도 매칭

### Q2: 어간 변화는 어떻게 작동하나요?

**A**: 자동으로 지원됩니다.
- `mirror` → `mirrors`, `mirrored`, `mirroring` 모두 매칭
- 패턴: `mirror(?:s|es|ed|ing|d)?`

### Q3: 와일드카드(`*`)는 언제 사용하나요?

**A**: 다양한 변형을 찾을 때 사용합니다.
- `duplicat*` → `duplicate`, `duplicates`, `duplication` 모두 매칭
- 정확한 어간을 모를 때 유용

### Q4: 점수가 1.0을 넘을 수 있나요?

**A**: 아니요. 최대값은 1.0입니다.
- `min(1.0, 계산된_점수)`로 제한됩니다

### Q5: 필드별 가중치는 왜 다른가요?

**A**: 중요도가 다르기 때문입니다.
- Customers, FE: 0.45 (가장 중요)
- Actions, Test: 0.05 (보조 정보)

### Q6: Stopwords는 무엇인가요?

**A**: 일반적인 단어들입니다.
- 예: `the`, `of`, `and`, `for` 등
- 의미 있는 키워드가 아니므로 제외됩니다

### Q7: 구문 키워드를 명시적으로 보호하려면?

**A**: 따옴표로 묶으세요.
```bash
--keywords 'femur,"femur length",range'
```

### Q8: Rule Score만 사용하려면?

**A**: `--alpha 1.0` 옵션을 사용하세요.
```bash
--alpha 1.0  # Rule Score만 사용 (Semantic Score 무시)
```

### Q9: Seeds는 토큰화된 키워드인가요?

**A**: 아니요. Seeds는 **처리 및 확장된 키워드 집합**입니다.
- 토큰화된 키워드도 포함하지만
- 구문 키워드도 그대로 포함합니다
- 개별 단어도 추가로 포함합니다

**예시**:
```
입력: "femur, femur length"
Seeds: ['femur', 'femur length', 'length']
      ↑        ↑                ↑
    원본    구문(그대로)      개별 단어(추가)
```

**코드 위치**: `hybrid_matcher.py` 124번 라인 주석 참고 ("씨앗(Seeds) 구성")

---

## 📊 요약 표

| 단계 | 입력 | 출력 | 코드 위치 |
|------|------|------|----------|
| 1. 파싱 | `"femur, femur length"` | `['femur', 'femur length']` | `hybrid_matcher.py` → `_parse_keywords()` |
| 2. Seeds 생성 | `['femur', 'femur length']` | `['femur', 'femur length', 'length']` | `hybrid_matcher.py` → `_build_config()` (124번 라인) |
| 3. 패턴 생성 | `['femur', 'femur length', 'length']` | `femur(?:s|es|ed|ing|d)?`, `femur\s+length` 등 | `keywords.py` → `_create_pattern()` |
| 4. 매칭 | 텍스트 + 패턴 | `['femur length']` | `keywords.py` → `extract_from_text()` |
| 5. 점수 계산 | 매칭 결과 | `symptom_score = 0.735` | `rules.py` → `calculate_symptom_score()` |
| 6. 최종 판정 | 점수 | `True/False/Review` | `combine.py` → `make_decision()` |

**참고**: Seeds는 단순히 토큰화된 키워드가 아니라, 구문 키워드 + 개별 단어가 모두 포함된 **처리 및 확장된 키워드 집합**입니다.

---

## 🎯 핵심 포인트

1. **Seeds의 정확한 의미**: Seeds는 단순히 "tokenized keywords"가 아니라, **처리 및 확장된 키워드 집합**입니다
   - 구문 키워드 그대로 포함
   - 개별 단어 추가
   - 토큰화된 키워드 포함
   - 와일드카드 보존
2. **키워드 확장**: 구문은 전체 + 개별 단어로 확장됩니다
3. **어간 변화 자동 지원**: 단어의 변형 형태도 자동으로 찾습니다
4. **구문 우선**: 긴 구문이 짧은 단어보다 우선 매칭됩니다
5. **필드별 가중치**: Customers와 FE 필드가 가장 중요합니다
6. **점수 제한**: 최대 점수는 1.0으로 제한됩니다

---

**작성일**: 2025-11-09  
**버전**: 1.0  
**작성자**: AI Assistant

