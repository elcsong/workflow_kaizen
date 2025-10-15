# 화학물질 데이터 ETL 모듈 설명서

이 문서는 `reach_etl.py`와 `kosha_etl.py` 두 개의 ETL(Extract, Transform, Load) 모듈에 대해 자세히 설명합니다. 각 모듈은 화학물질 안전 데이터를 자동으로 수집하고 처리하는 파이프라인입니다.

## 목차
1. [EU REACH ETL 모듈 (reach_etl.py)](#eu-reach-etl-모듈-reach_etlpy)
2. [한국 KOSHA ETL 모듈 (kosha_etl.py)](#한국-kosha-etl-모듈-kosha_etlpy)
3. [공통 특징 및 사용법](#공통-특징-및-사용법)

---

## EU REACH ETL 모듈 (reach_etl.py)

### 개요
EU REACH(Registration, Evaluation, Authorisation and Restriction of Chemicals) 규제에서 관리하는 화학물질 데이터를 자동으로 수집하는 ETL 파이프라인입니다.

### 대상 데이터
- **SVHC (Candidate List)**: 후보 물질 목록
- **Annex XIV**: 승인 대상 물질 목록
- **Annex XVII**: 제한 물질 목록

### ETL 프로세스 상세 설명

#### 1. Extract (추출) 단계
```python
# Selenium을 사용하여 ECHA 웹사이트에서 데이터 다운로드
download_xml_selenium(annex_type)
```

**동작 방식:**
- Selenium WebDriver를 사용하여 Chrome/Edge 브라우저를 자동 제어
- ECHA(European Chemicals Agency) 웹사이트 접속
- 이용 약관 동의 및 쿠키 배너 처리
- XML 다운로드 버튼 클릭 및 파일 다운로드 대기
- 다운로드 완료까지 자동으로 대기

**설정된 URL들:**
- SVHC: `https://echa.europa.eu/candidate-list-table`
- Annex XIV: `https://echa.europa.eu/authorisation-list`
- Annex XVII: `https://echa.europa.eu/substances-restricted-under-reach`

#### 2. Transform (변환) 단계
```python
# XML 데이터를 파싱하여 구조화된 데이터로 변환
tree = ET.parse(xml_file)
root = tree.getroot()
for row in root.findall('.//result'):
    # XML 요소를 딕셔너리로 변환
```

**처리 내용:**
- XML 파일을 파싱하여 각 물질의 정보를 추출
- 물질명, CAS 번호, 화학식, 위험 분류 등의 정보를 정제
- 표준화된 데이터 구조로 변환

#### 3. Load (적재) 단계
```python
# JSON 형식으로 저장
json_file = 'data/reach_data.json'
with open(json_file, 'w') as f:
    json.dump(all_data, f, indent=4)
```

**저장 위치:** `data/reach_data.json`

### 데이터 구조 예시
```json
{
  "svhc": {
    "metadata": {
      "annex_type": "svhc",
      "item_count": 235,
      "source": "https://echa.europa.eu/candidate-list-table"
    },
    "data": [
      {
        "name": "Bis(2-ethylhexyl) phthalate",
        "cas_number": "117-81-7",
        "ec_number": "204-211-0"
      }
    ]
  }
}
```

### 실행 방법
```bash
# 기본 실행 (모든 Annex 데이터 수집)
python modules/etl-pipeline/reach_etl.py

# 기존 파일 사용 (다운로드 생략)
python modules/etl-pipeline/reach_etl.py --skip-download
```

---

## 한국 KOSHA ETL 모듈 (kosha_etl.py)

### 개요
한국 산업안전보건법에서 관리하는 특수관리물질 및 유해화학물질 데이터를 자동으로 수집하는 ETL 파이프라인입니다.

### 대상 데이터
- **special_materials**: 산업안전보건법 제41조 특수관리물질
- **hazardous_materials**: 화학물질안전원 유해화학물질
- **mole_data**: 고용노동부 화학물질 안전 데이터

### ETL 프로세스 상세 설명

#### 1. Extract (추출) 단계

##### 1.1 API 추출 시도
```python
# API 엔드포인트들을 순차적으로 시도
api_endpoints = [
    f"{api_base}/list",      # 목록 조회
    f"{api_base}/data",      # 데이터 조회
    f"{api_base}/chemicals", # 화학물질 데이터
    f"{api_base}/substances" # 물질 데이터
]
```

##### 1.2 웹 스크래핑 추출
```python
# Selenium을 사용하여 웹사이트 탐색
search_kosha_data(data_type)
```

**동작 방식:**
- 여러 기관의 웹사이트를 순차적으로 탐색
- 쿠키 동의 배너 자동 처리
- 엑셀, CSV, PDF 다운로드 링크 검색
- HTML 테이블 데이터 추출

**설정된 기관 및 URL들:**
- **KOSHA**: `https://www.kosha.or.kr/kosha/index.do`
- **NICS**: `https://www.nics.go.kr/`
- **고용노동부**: `https://www.moel.go.kr/`

##### 1.3 샘플 데이터 사용 (개발용)
```python
# 실제 데이터 수집 실패 시 샘플 데이터 사용
_get_sample_special_materials_data()
```

#### 2. Transform (변환) 단계
```python
# 다양한 형식의 데이터를 표준화
def _read_excel_robust(path: str) -> pd.DataFrame:
    # 한글 인코딩 지원 (cp949, euc-kr 등)
```

**처리 내용:**
- 엑셀 파일: `openpyxl` 또는 `xlrd` 엔진 사용
- CSV 파일: 다양한 인코딩 시도 (utf-8, cp949, euc-kr 등)
- HTML 테이블: Selenium으로 추출 후 DataFrame 변환
- 데이터 정제 및 표준화

#### 3. Load (적재) 단계
```python
# JSON 형식으로 저장
output_file = f'data/{args.output_file}'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=4, ensure_ascii=False)
```

**저장 위치:** `data/kosha_data.json` (기본값)

### 데이터 구조 예시
```json
{
  "metadata": {
    "data_type": "special_materials",
    "source": "sample_data",
    "item_count": 5,
    "note": "This is sample data for development. Replace with actual data extraction.",
    "config": {
      "name": "특수관리물질",
      "description": "산업안전보건법 제41조에 따른 특수관리물질 목록"
    }
  },
  "data": [
    {
      "물질명": "벤젠",
      "영문명": "Benzene",
      "CAS_No": "71-43-2",
      "관리기준": "피부흡수방지, 호흡기보호구 착용",
      "관리방법": "노출한계: 1ppm, 생물학적노출지표 모니터링",
      "비고": "발암성 물질"
    }
  ]
}
```

### 실행 방법
```bash
# 특수관리물질 데이터 수집 (샘플 데이터 사용)
python modules/etl-pipeline/kosha_etl.py --data-type special_materials --skip-download

# 유해화학물질 데이터 수집
python modules/etl-pipeline/kosha_etl.py --data-type hazardous_materials

# 고용노동부 데이터 수집, 결과 파일명 지정
python modules/etl-pipeline/kosha_etl.py --data-type mole_data --output-file custom_kosha_data.json
```

---

## 공통 특징 및 사용법

### 기술 스택
- **Python 3.9+**
- **Selenium**: 웹 자동화
- **Pandas**: 데이터 처리
- **Requests**: HTTP 요청
- **BeautifulSoup**: HTML 파싱
- **OpenPyXL/XLRD**: 엑셀 파일 처리

### 설치 요구사항
```bash
pip install selenium pandas requests beautifulsoup4 lxml openpyxl xlrd webdriver-manager
```

### 브라우저 자동화
- **Chrome/Edge WebDriver** 자동 설치 (`webdriver-manager`)
- **헤드리스 모드**로 백그라운드 실행
- **쿠키 배너** 자동 처리
- **다국어 지원** (영어/한국어)

### 에러 처리 및 복원력
- **다중 재시도** 메커니즘
- **대안 데이터 소스** 활용
- **샘플 데이터 폴백** (개발용)
- **상세 로깅** 및 오류 메시지

### 데이터 저장 형식
- **JSON 형식**으로 통일 저장
- **UTF-8 인코딩** (한글 지원)
- **메타데이터 포함** (출처, 수집일시, 항목수 등)
- **구조화된 데이터** (표준화된 필드명)

### 사용 시나리오
1. **개발/테스트**: `--skip-download` 옵션으로 샘플 데이터 사용
2. **실제 운영**: 실제 웹사이트에서 최신 데이터 수집
3. **정기 업데이트**: 스케줄러와 연동하여 자동 업데이트
4. **데이터 분석**: 수집된 JSON 데이터를 분석 도구로 활용

### 주의사항
- **네트워크 연결** 필요 (실제 데이터 수집 시)
- **웹사이트 변경** 가능성 (주기적 모니터링 필요)
- **법적 준수**: 공공 데이터 활용 시 이용 약관 준수
- **속도 제한**: 과도한 요청 방지를 위한 딜레이 적용

---

## 결론

두 ETL 모듈은 화학물질 안전 데이터를 자동으로 수집하고 표준화된 형식으로 저장하는 강력한 도구입니다. EU REACH 모듈은 유럽 화학물질 규제 데이터를, KOSHA 모듈은 한국 산업안전 데이터를 각각 전문적으로 처리합니다.

각 모듈은 웹 스크래핑, API 호출, 파일 다운로드 등 다양한 방법을 조합하여 최대한 많은 데이터를 확보하며, 실패 시에도 샘플 데이터를 통해 개발 및 테스트를 지원합니다.
