# 🚀 초보자를 위한 완전 가이드

## 📋 목차
1. [환경 설정](#1-환경-설정)
2. [기본 사용법](#2-기본-사용법)
3. [실전 예시](#3-실전-예시)
4. [결과 해석](#4-결과-해석)
5. [문제 해결](#5-문제-해결)

---

## 1. 환경 설정

### 1.1 필수 프로그램 설치

#### ✅ Python 3.8+ 설치
```bash
# Windows에서 Python 다운로드
# https://www.python.org/downloads/ 에서 최신 버전 다운로드
```

#### ✅ 가상환경 생성 및 활성화
```bash
# 1. 프로젝트 폴더로 이동
cd C:\project

# 2. 가상환경 생성
python -m venv cvenv

# 3. 가상환경 활성화 (Windows)
cvenv\Scripts\activate

# 4. 패키지 설치
pip install pandas openpyxl sentence-transformers torch transformers pyyaml numpy
```

### 1.2 설치 확인
```bash
# Python 버전 확인
python --version

# 패키지 설치 확인
python -c "import pandas, openpyxl; print('✅ 설치 완료!')"
```

---

## 2. 기본 사용법

### 2.1 하이브리드 분석 (추천 방식)

**🎯 용도**: Excel 파일에서 특정 문제와 유사한 케이스를 찾고 싶을 때

#### 기본 명령어 구조
```bash
python -m intent_matcher.cli.hybrid_match \
    --file [Excel파일경로] \
    --target-id [기준이되는ID] \
    --keywords [필터링키워드들] \
    --output [결과파일명]
```

#### 📝 실제 사용 예시
```bash
# 예시 1: 크리스탈 관련 문제 찾기
python -m intent_matcher.cli.hybrid_match \
    --file complaints_data.xlsx \
    --target-id COM-21912149 \
    --keywords crystal,artifact,probe \
    --output crystal_analysis.xlsx

# 예시 2: 혈류 관련 문제 찾기  
python -m intent_matcher.cli.hybrid_match \
    --file complaints_data.xlsx \
    --target-id COM-22001003 \
    --keywords blood,flow,doppler \
    --output blood_flow_analysis.xlsx
```

### 2.2 매개변수 설명

| 매개변수 | 필수여부 | 설명 | 예시 |
|---------|---------|------|------|
| `--file` | ✅ 필수 | 분석할 Excel 파일 경로 | `data.xlsx` |
| `--target-id` | ✅ 필수 | 기준이 되는 불만 ID | `COM-21912149` |
| `--keywords` | ✅ 필수 | 1차 필터링 키워드 (쉼표로 구분) | `crystal,probe,artifact` |
| `--output` | ⚡ 선택 | 결과 파일명 (기본: `hybrid_analysis_결과.xlsx`) | `my_result.xlsx` |
| `--use-sbert` | ⚡ 선택 | AI 의미 분석 사용 (기본: 비사용) | (플래그만 추가) |
| `--threshold` | ⚡ 선택 | 유사도 임계값 (기본: 0.55) | `--threshold 0.6` |
| `--alpha` | ⚡ 선택 | 규칙:의미 비율 (기본: 0.5) | `--alpha 0.7` |

---

## 3. 실전 예시

### 3.1 데모 데이터로 연습하기

#### 📊 1단계: 데모 데이터 생성
```bash
# 연습용 Excel 파일 생성
python create_demo_data.py
```
**결과**: `demo_complaints_20250821_HHMMSS.xlsx` 파일 생성

#### 🔍 2단계: 기본 분석 실행

**⚠️ 실행 방법 주의사항**: 모듈 실행(`-m` 옵션)에서 인수 인식 오류가 발생할 수 있습니다.

**권장 방법 1: 직접 파일 실행**
```bash
# 생성된 파일명으로 분석 실행 (파일명은 실제 생성된 것으로 변경)
python intent_matcher/cli/hybrid_match.py \
    --file demo_complaints_20250821_212547.xlsx \
    --target-id COM-21912149 \
    --keywords crystal,artifact,probe \
    --output my_first_analysis.xlsx
```

**권장 방법 2: 가상환경 Python 직접 사용**
```bash
# 가상환경 활성화 없이 직접 실행
cvenv\Scripts\python.exe intent_matcher/cli/hybrid_match.py \
    --file demo_complaints_20250821_212547.xlsx \
    --target-id COM-21912149 \
    --keywords crystal,artifact,probe \
    --output my_first_analysis.xlsx
```

**대안: 모듈 실행 (패키지 설치 후)**
```bash
# 먼저 패키지를 설치하면 모듈 실행이 가능합니다
cvenv\Scripts\python.exe -m pip install -e .

# 그 다음 모듈로 실행
python -m intent_matcher.cli.hybrid_match \
    --file demo_complaints_20250821_212547.xlsx \
    --target-id COM-21912149 \
    --keywords crystal,artifact,probe \
    --output my_first_analysis.xlsx
```

#### 📈 3단계: AI 의미 분석 추가
```bash
# SBERT를 사용한 고급 분석 (직접 파일 실행 방식)
python intent_matcher/cli/hybrid_match.py \
    --file demo_complaints_20250821_212547.xlsx \
    --target-id COM-21912149 \
    --keywords crystal,artifact,probe \
    --use-sbert \
    --output advanced_analysis.xlsx
```

### 3.2 실제 데이터 분석 예시

#### 📋 Excel 파일 준비
Excel 파일에 다음 컬럼들이 있어야 합니다:
- `Complaint ID`: 불만 식별자
- `Customers Issue Description(Full)`: 고객 문제 설명
- `FE's Issue Description(Full)`: 필드 엔지니어 설명  
- `Actions Taken / Repairs(Full)`: 수행한 조치
- `Repair Test / Inspection Data(Full)`: 테스트/검사 데이터

#### 🎯 단계별 분석 과정

**1단계: 탐색적 분석**
```bash
# 넓은 키워드로 1차 탐색 (직접 파일 실행 방식)
python intent_matcher/cli/hybrid_match.py \
    --file real_data.xlsx \
    --target-id COM-REFERENCE-001 \
    --keywords error,problem,issue,fault \
    --threshold 0.4 \
    --output exploration.xlsx
```

**2단계: 정밀 분석**
```bash
# 구체적 키워드로 정밀 분석 (직접 파일 실행 방식)
python intent_matcher/cli/hybrid_match.py \
    --file real_data.xlsx \
    --target-id COM-REFERENCE-001 \
    --keywords crystal,transducer,beamformer \
    --use-sbert \
    --threshold 0.6 \
    --output precise_analysis.xlsx
```

---

## 4. 결과 해석

### 4.1 출력 파일 구조

분석 완료 후 다음과 같은 Excel 파일이 생성됩니다:

```
📊 결과파일.xlsx
├── 📋 Analysis_Results      # 주요 분석 결과
├── ⚙️  Analysis_Settings    # 분석 설정 정보
├── 🎯 Target_Configuration  # 타겟에서 추출된 설정
├── 📊 Keyword_Statistics    # 키워드별 매칭 통계
└── 📈 Analysis_Statistics   # 전체 분석 통계
```

### 4.2 주요 컬럼 설명

#### Analysis_Results 시트의 핵심 컬럼들:

| 컬럼명 | 설명 | 해석 방법 |
|--------|------|-----------|
| `SameDefect` | 동일 유형 판정 | `True`: 같은 문제, `False`: 다른 문제, `Review`: 검토 필요 |
| `FinalScore` | 최종 유사도 점수 | 0.0~1.0 (높을수록 유사) |
| `Filter_Keywords_Found` | 매칭된 키워드 목록 | 어떤 키워드가 발견되었는지 |
| `Filter_Context` | 키워드 발견 문맥 | **키워드가 어떤 맥락에서 나타났는지** (굵게 표시됨) |
| `Filter_Details` | 상세 매칭 정보 | JSON 형태의 키워드 매칭 세부사항 |
| `Reasoning` | 판정 근거 | 왜 이런 판정을 내렸는지 설명 |

### 4.3 점수 해석 가이드

#### 🎯 FinalScore 해석
```
0.8 ~ 1.0  ✅ 매우 유사 (거의 동일한 문제)
0.6 ~ 0.8  ⚡ 유사 (관련성 높음)
0.4 ~ 0.6  ⚠️ 보통 (일부 관련성)
0.2 ~ 0.4  🔍 약한 관련성
0.0 ~ 0.2  ❌ 관련성 낮음
```

#### 📋 SameDefect 판정 기준
- **True**: FinalScore > threshold (기본 0.55)
- **Review**: FinalScore가 threshold 근처 (±0.1 범위)
- **False**: FinalScore < threshold

---

## 5. 문제 해결

### 5.1 자주 발생하는 오류들

#### ❌ `ModuleNotFoundError: No module named 'pandas'`
```bash
# 해결방법: 가상환경 활성화 후 패키지 재설치
cvenv\Scripts\activate
pip install pandas openpyxl
```

#### ❌ `FileNotFoundError: [Errno 2] No such file or directory`
```bash
# 해결방법: 파일 경로 확인
dir *.xlsx  # Excel 파일들 확인
# 정확한 파일명으로 다시 실행
```

#### ❌ `KeyError: 'Complaint ID'`
```bash
# 해결방법: Excel 파일의 컬럼명 확인
# 필요한 컬럼들:
# - Complaint ID
# - Customers Issue Description(Full)  
# - FE's Issue Description(Full)
# - Actions Taken / Repairs(Full)
# - Repair Test / Inspection Data(Full)
```

#### ❌ `No records matched the filter keywords`
```bash
# 해결방법: 키워드를 더 일반적으로 변경하거나 threshold 낮추기
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx \
    --target-id COM-123 \
    --keywords problem,issue,error \
    --threshold 0.3
```

### 5.2 성능 최적화 팁

#### ⚡ 빠른 분석을 위한 설정
```bash
# SBERT 없이 실행 (빠름)
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx \
    --target-id COM-123 \
    --keywords key1,key2 \
    --output quick_result.xlsx
```

#### 🎯 정확한 분석을 위한 설정
```bash
# SBERT 포함 실행 (느리지만 정확)
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx \
    --target-id COM-123 \
    --keywords key1,key2 \
    --use-sbert \
    --threshold 0.6 \
    --output accurate_result.xlsx
```

### 5.3 임계값 설정으로 분석 정확도 높이기 ⭐NEW!

이제 분석 중에 임계값을 자유롭게 조정할 수 있습니다!

#### 🎯 기본 사용법
```bash
# 기존 방식 (고정 임계값)
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "error,issue"

# 새로운 방식 (임계값 조정 가능)
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "error,issue" \
    --min-score 0.8 --review-band 0.7,0.8 --require-symptom false
```

#### 📊 상황별 임계값 설정

**1️⃣ 엄격한 기준이 필요한 경우**
- 고품질 매칭만 원할 때
- 거짓 양성(False Positive)을 최소화하고 싶을 때

```bash
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "critical,severe" \
    --min-score 0.85 \        # 높은 임계값
    --review-band 0.8,0.85 \  # 좁은 리뷰 구간
    --require-symptom true \  # 증상 필수
    --alpha 0.7              # 룰 기반 중심
```

**2️⃣ 관대한 기준이 필요한 경우**  
- 더 많은 후보를 찾고 싶을 때
- 놓치는 케이스(False Negative)를 최소화하고 싶을 때

```bash
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "issue,problem" \
    --min-score 0.5 \         # 낮은 임계값
    --review-band 0.4,0.5 \   # 넓은 리뷰 구간  
    --require-symptom false \ # 증상 선택적
    --alpha 0.3              # 의미 분석 중심
```

**3️⃣ 균형잡힌 설정 (권장)**
- 대부분의 상황에 적합한 설정

```bash
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "error,issue" \
    --min-score 0.7 \         # 중간 임계값
    --review-band 0.6,0.7 \   # 표준 리뷰 구간
    --require-symptom true \  # 증상 필수
    --use-sbert              # SBERT 포함
```

#### 🔧 주요 옵션 설명

| 옵션 | 설명 | 예시 |
|------|------|------|
| `--min-score` | True 판정을 위한 최소 점수 | `0.8` (엄격) ~ `0.5` (관대) |
| `--review-band` | 인간 검토가 필요한 점수 구간 | `0.7,0.8` |
| `--require-symptom` | 증상 키워드 반드시 필요 | `true` / `false` |
| `--alpha` | 룰 vs 의미 점수 비율 | `0.7` (룰 중심) ~ `0.3` (의미 중심) |

#### 💡 실전 팁

**Step 1: 넓은 그물로 시작**
```bash
# 1단계: 관대한 기준으로 후보 찾기
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "issue" \
    --min-score 0.5 --output step1_candidates.xlsx
```

**Step 2: 점차 기준 엄격화**
```bash
# 2단계: 엄격한 기준으로 정제
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "critical,issue" \
    --min-score 0.8 --require-symptom true --output step2_final.xlsx
```

**Step 3: 결과 비교 분석**
```bash
# 여러 임계값으로 실험해보기
for threshold in 0.5 0.6 0.7 0.8; do
    python -m intent_matcher.cli.hybrid_match \
        --file data.xlsx --target-id COM-123 --keywords "issue" \
        --min-score $threshold --output "result_$threshold.xlsx"
done
```

#### 🎛️ 고급 설정 조합

**의미 분석 중심 설정 (정확하지만 느림)**
```bash
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "issue" \
    --use-sbert --alpha 0.2 --min-score 0.6
```

**룰 기반 중심 설정 (빠르지만 단순함)**
```bash  
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "issue" \
    --alpha 0.9 --min-score 0.7 --require-symptom true
```

**실험용 설정 (다양한 결과 확인)**
```bash
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx --target-id COM-123 --keywords "issue" \
    --min-score 0.4 --review-band 0.3,0.8 --require-symptom false
```

📖 **더 자세한 가이드**: [THRESHOLD_CONFIGURATION.md](THRESHOLD_CONFIGURATION.md)

### 5.4 키워드 선택 가이드

#### ✅ 좋은 키워드 예시
```bash
# 구체적이고 기술적인 용어
--keywords crystal,transducer,beamformer,artifact

# 증상 관련 키워드
--keywords noise,distortion,failure,malfunction

# 부품/컴포넌트 키워드  
--keywords probe,cable,connector,board
```

#### ❌ 피해야 할 키워드
```bash
# 너무 일반적인 단어들
--keywords problem,issue,error,bad  # 너무 광범위

# 너무 짧은 단어들
--keywords a,is,the,and  # 의미 없음
```

---

## 6. 고급 사용법

### 6.1 배치 처리 예시

여러 타겟 ID를 순차적으로 분석하고 싶을 때:

```bash
# batch_analysis.bat 파일 생성
@echo off
echo 배치 분석 시작...

python -m intent_matcher.cli.hybrid_match --file data.xlsx --target-id COM-001 --keywords crystal,probe --output result_001.xlsx
python -m intent_matcher.cli.hybrid_match --file data.xlsx --target-id COM-002 --keywords blood,flow --output result_002.xlsx  
python -m intent_matcher.cli.hybrid_match --file data.xlsx --target-id COM-003 --keywords noise,artifact --output result_003.xlsx

echo 배치 분석 완료!
pause
```

### 6.2 결과 병합 스크립트

```python
# merge_results.py
import pandas as pd
import glob

# 모든 결과 파일 찾기
result_files = glob.glob("result_*.xlsx")

# 결과 병합
all_results = []
for file in result_files:
    df = pd.read_excel(file, sheet_name='Analysis_Results')
    df['Source_File'] = file
    all_results.append(df)

# 통합 결과 저장
merged_df = pd.concat(all_results, ignore_index=True)
merged_df.to_excel('merged_analysis_results.xlsx', index=False)
print(f"✅ {len(result_files)}개 파일 병합 완료!")
```

---

## 📞 도움이 더 필요하다면

### 📚 추가 문서들
- `MANUAL_SETUP_GUIDE.md`: 상세 설치 가이드
- `README.md`: 프로젝트 개요
- `SBERT_OFFLINE_USAGE_GUIDE.md`: SBERT 오프라인 사용법

### 🔧 디버깅 도구들
```bash
# 로그 레벨 높이기 (더 자세한 정보)
python -m intent_matcher.cli.hybrid_match \
    --file data.xlsx \
    --target-id COM-123 \
    --keywords test \
    --output debug.xlsx \
    2> debug.log  # 오류 로그 저장
```

### ✅ 성공적인 분석을 위한 체크리스트
- [ ] Python 3.8+ 설치됨
- [ ] 가상환경 활성화됨  
- [ ] 필요한 패키지 설치됨
- [ ] Excel 파일에 필수 컬럼들 존재
- [ ] target-id가 Excel 파일에 존재
- [ ] 적절한 키워드 선택됨
- [ ] 충분한 디스크 공간 확보

---

🎉 **이제 분석을 시작해보세요!** 

작은 데모 데이터부터 시작해서 점차 실제 데이터로 확장해나가시면 됩니다.
