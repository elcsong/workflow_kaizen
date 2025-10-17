# RoHS Compliance ETL User Guide

## 개요

이 가이드는 RoHS (Restriction of Hazardous Substances) 컴플라이언스 데이터를 JSON 형식으로 ETL(Extract, Transform, Load)하고 수동으로 업데이트하는 방법을 설명합니다.

## 목차

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 및 설정](#설치-및-설정)
3. [JSON 데이터 구조](#json-데이터-구조)
4. [ETL 프로세스 실행](#etl-프로세스-실행)
5. [웹 데이터 수집](#웹-데이터-수집)
6. [수동 업데이트 방법](#수동-업데이트-방법)
7. [데이터 검증](#데이터-검증)
8. [API 사용 예제](#api-사용-예제)
9. [문제 해결](#문제-해결)
10. [버전 관리](#버전-관리)

## 시스템 요구사항

- Python 3.8 이상
- 표준 라이브러리 (json, csv, argparse, pathlib, logging, datetime)
- 웹 데이터 수집용 추가 라이브러리 (선택사항):
  - requests: HTTP 요청
  - beautifulsoup4: HTML 파싱
  - lxml: XML/HTML 파서
  - feedparser: RSS 피드 파싱

## 설치 및 설정

### 1. 프로젝트 구조

프로젝트는 다음과 같은 구조를 가집니다:

```
win_workflow_kaizen/
├── scripts/
│   └── rohs_etl.py          # 메인 ETL 스크립트
├── data/
│   └── json/                # JSON 출력 파일 저장 디렉토리
├── docs/
│   └── rohs-etl-user-guide.md  # 이 문서
└── requirements.txt         # Python 의존성
```

### 2. 실행 권한 설정

```bash
chmod +x scripts/rohs_etl.py
```

## JSON 데이터 구조

### 전체 구조

```json
{
  "metadata": {
    "version": "1.0",
    "last_updated": "2025-01-01 12:00:00",
    "source": "Web search compilation and manual verification",
    "notes": "All concentration limits are 0.1% for Pb/Hg/Cr6+/PBB/PBDE/DEHP/BBP/DBP/DIBP, 0.01% for Cd unless otherwise noted. True=restricted, False=not restricted, None=unknown",
    "substances": ["Pb", "Hg", "Cd", "Cr6+", "PBB", "PBDE", "DEHP", "BBP", "DBP", "DIBP"],
    "total_countries": 17
  },
  "countries": {
    "EU": {
      "name": "European Union",
      "regulation": "RoHS 3 (Directive 2015/863)",
      "restrictions": {
        "Pb": true,
        "Hg": true,
        "Cd": true,
        "Cr6+": true,
        "PBB": true,
        "PBDE": true,
        "DEHP": true,
        "BBP": true,
        "DBP": true,
        "DIBP": true
      },
      "notes": "Global standard (RoHS 3)",
      "last_updated": "2025-01-01"
    }
  }
}
```

### 필드 설명

#### Metadata
- `version`: 데이터 버전
- `last_updated`: 마지막 업데이트 일시
- `source`: 데이터 출처
- `notes`: 중요 참고사항
- `substances`: 추적하는 제한 물질 목록
- `total_countries`: 총 국가 수

#### Countries
- `name`: 국가명 (전체 이름)
- `regulation`: 해당 규제명
- `restrictions`: 물질별 제한 여부
  - `true`: 제한됨
  - `false`: 제한되지 않음
  - `null`: 정보 불명
- `notes`: 추가 참고사항
- `last_updated`: 국가별 마지막 업데이트 일자

### 제한 물질 코드

| 코드 | 물질명 | 일반 농도 한도 |
|------|--------|---------------|
| Pb | 납 (Lead) | 0.1% |
| Hg | 수은 (Mercury) | 0.1% |
| Cd | 카드뮴 (Cadmium) | 0.01% |
| Cr6+ | 6가 크롬 (Hexavalent Chromium) | 0.1% |
| PBB | 폴리브롬화 바이페닐 (Polybrominated Biphenyls) | 0.1% |
| PBDE | 폴리브롬화 디페닐 에테르 (Polybrominated Diphenyl Ethers) | 0.1% |
| DEHP | 비스(2-에틸헥실) 프탈레이트 | 0.1% |
| BBP | 부틸 벤질 프탈레이트 | 0.1% |
| DBP | 디부틸 프탈레이트 | 0.1% |
| DIBP | 디이소부틸 프탈레이트 | 0.1% |

## ETL 프로세스 실행

### 기본 ETL 실행

수동 데이터를 사용하여 JSON 생성:

```bash
python scripts/rohs_etl.py
```

### CSV 파일로부터 ETL 실행

CSV 파일이 있는 경우:

```bash
python scripts/rohs_etl.py --csv data/rohs_matrix.csv
```

### 출력 파일 지정

```bash
python scripts/rohs_etl.py --output data/json/rohs_custom.json
```

### 웹 데이터 포함 ETL 실행

공식 웹사이트에서 최신 데이터를 자동으로 가져와서 포함:

```bash
python scripts/rohs_etl.py --web-data
```

웹 데이터와 CSV 데이터를 함께 사용:

```bash
python scripts/rohs_etl.py --csv data/rohs_matrix.csv --web-data
```

### CSV 파일 형식

ETL 시스템은 CSV 파일을 통해 외부 데이터를 쉽게 가져올 수 있습니다. CSV 파일은 Microsoft Excel, Google Sheets, 또는 일반 텍스트 편집기로 생성할 수 있습니다.

#### 필수 형식 및 구조

CSV 파일의 첫 번째 줄은 **헤더(header)**여야 하며, 두 번째 줄부터는 실제 데이터가 옵니다. 인코딩은 **UTF-8**을 권장합니다.

```csv
Country_Code,Country_Name,Regulation,Pb,Hg,Cd,Cr6+,PBB,PBDE,DEHP,BBP,DBP,DIBP,Notes,Last_Updated
EU,European Union,RoHS 3 (Directive 2015/863),1,1,1,1,1,1,1,1,1,1,Global standard (RoHS 3),2025-01-01
CN,China,China RoHS 2 (GB 26572-2025),1,1,1,1,1,1,1,1,1,1,Phthalates 4 added from 2026-01-01,2025-01-01
US-CA,California, US,Electronic Waste Recycling Act,1,1,1,1,0,0,0,0,0,0,Only 4 heavy metals, mainly for video displays,2025-01-01
```

#### 필드 설명

| 필드명 | 필수여부 | 데이터 타입 | 설명 | 허용 값 | 예시 |
|--------|----------|-------------|------|----------|------|
| `Country_Code` | 필수 | 문자열 | ISO 3166-1 alpha-2 형식의 국가 코드 | 2자리 대문자 | `EU`, `CN`, `US`, `KR` |
| `Country_Name` | 필수 | 문자열 | 국가의 전체 이름 | 자유 텍스트 | `European Union`, `China`, `United States` |
| `Regulation` | 필수 | 문자열 | 해당 국가의 RoHS 규제명 | 자유 텍스트 | `RoHS 3 (Directive 2015/863)`, `China RoHS 2` |
| `Pb` | 필수 | 숫자 | 납(Pb) 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `Hg` | 필수 | 숫자 | 수은(Hg) 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `Cd` | 필수 | 숫자 | 카드뮴(Cd) 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `Cr6+` | 필수 | 숫자 | 6가 크롬(Cr6+) 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `PBB` | 필수 | 숫자 | PBB 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `PBDE` | 필수 | 숫자 | PBDE 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `DEHP` | 필수 | 숫자 | DEHP 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `BBP` | 필수 | 숫자 | BBP 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `DBP` | 필수 | 숫자 | DBP 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `DIBP` | 필수 | 숫자 | DIBP 제한 여부 | `1`(제한), `0`(미제한), 빈 값(알 수 없음) | `1` |
| `Notes` | 선택 | 문자열 | 추가 참고사항 | 자유 텍스트 | `Global standard (RoHS 3)` |
| `Last_Updated` | 선택 | 날짜 | 마지막 업데이트 일자 | YYYY-MM-DD 형식 | `2025-01-01` |

#### 제한 물질 값 상세 설명

각 물질 필드의 값은 다음을 의미합니다:

- **`1` (또는 `true`)**: 해당 물질이 RoHS에서 제한됨
- **`0` (또는 `false`)**: 해당 물질이 RoHS에서 제한되지 않음
- **빈 값 (empty)**: 정보가 불충분하거나 알 수 없음

**농도 한도 참고:**
- 카드뮴(Cd)을 제외한 모든 물질: 0.1% (균질 재료 기준)
- 카드뮴(Cd): 0.01% (균질 재료 기준)

#### CSV 파일 생성 예시

##### Microsoft Excel에서 생성하기

1. Excel을 열고 첫 번째 행에 헤더를 입력합니다:
   ```
   Country_Code | Country_Name | Regulation | Pb | Hg | Cd | Cr6+ | PBB | PBDE | DEHP | BBP | DBP | DIBP | Notes | Last_Updated
   ```

2. 두 번째 행부터 데이터를 입력합니다.

3. 파일을 **CSV UTF-8** 형식으로 저장합니다.

##### Google Sheets에서 생성하기

1. Google Sheets에서 새 스프레드시트를 만듭니다.

2. 첫 번째 행에 헤더를 입력합니다.

3. 데이터를 입력합니다.

4. **파일 > 다운로드 > 쉼표로 구분된 값(.csv)**으로 저장합니다.

##### 텍스트 편집기로 직접 생성하기

```csv
Country_Code,Country_Name,Regulation,Pb,Hg,Cd,Cr6+,PBB,PBDE,DEHP,BBP,DBP,DIBP,Notes,Last_Updated
EU,European Union,"RoHS 3 (Directive 2015/863)",1,1,1,1,1,1,1,1,1,1,"Global standard (RoHS 3)",2025-01-01
CN,China,"China RoHS 2 (GB 26572-2025)",1,1,1,1,1,1,1,1,1,1,"Phthalates 4 added from 2026-01-01",2025-01-01
KR,"South Korea","Korea RoHS",1,1,1,1,1,1,1,1,1,1,"Resource Circulation Act",2025-01-01
```

**주의사항:**
- 큰따옴표로 묶인 텍스트는 쉼표를 포함할 수 있습니다.
- 날짜는 반드시 `YYYY-MM-DD` 형식을 사용해야 합니다.

#### CSV 파일 검증

CSV 파일을 ETL에 사용하기 전에 다음 사항을 확인하세요:

1. **헤더 확인**: 모든 필수 필드가 정확히 입력되었는지 확인
2. **데이터 타입**: 숫자 필드에 텍스트가 없는지 확인
3. **인코딩**: UTF-8로 저장되었는지 확인
4. **특수 문자**: 텍스트 필드의 큰따옴표와 쉼표 처리 확인

#### CSV 파일 사용 예시

```bash
# CSV 파일로 ETL 실행
python scripts/rohs_etl.py --csv data/rohs_custom_data.csv

# CSV + 웹 데이터 결합
python scripts/rohs_etl.py --csv data/rohs_custom_data.csv --web-data
```

### JSON 파일 자동 선택

ETL 시스템은 `data/json/` 폴더에서 최신 RoHS JSON 파일을 자동으로 선택합니다:

```bash
# 최신 JSON 파일을 자동으로 선택하여 요약 표시
python scripts/rohs_etl.py --action summary

# 최신 JSON 파일을 자동으로 선택하여 수동 업데이트
python scripts/rohs_etl.py --action update --country CN --substance DEHP --restricted true
```

#### 파일 선택 우선순위

1. **명시적 지정**: `--update` 옵션으로 특정 파일 지정 시 해당 파일 사용
2. **자동 선택**: 파일 미지정 시 `data/json/` 폴더에서 최신 파일 자동 선택
   - 파일명 패턴: `rohs_*.json`
   - 정렬 기준: 파일 수정 시간 (최신 파일 우선)

**예시 파일 목록:**
```
data/json/
├── rohs_compliance_data_20251017_185411.json  # 기본 ETL 결과
└── rohs_web_etl_test.json                     # 웹 데이터 포함 ETL 결과 (최신)
```

위 경우 `--action summary` 실행 시 `rohs_web_etl_test.json`이 자동 선택됩니다.

## 웹 데이터 수집

ETL 시스템은 공식 웹사이트, 검색 엔진, RSS 피드에서 최신 RoHS 규제 정보를 자동으로 수집할 수 있습니다.

### 웹 소스에서 데이터 가져오기

#### 모든 웹 소스에서 데이터 수집

```bash
python scripts/rohs_etl.py --action web-fetch
```

#### 특정 웹 소스에서만 데이터 수집

```bash
# EU RoHS 데이터만 가져오기
python scripts/rohs_etl.py --action web-fetch --source eu_rohs

# 중국 RoHS 데이터만 가져오기
python scripts/rohs_etl.py --action web-fetch --source china_rohs
```

#### 사용 가능한 웹 소스

`--web-data` 옵션 사용 시 다음 공식 웹사이트에서 데이터를 파싱합니다:

| 소스 코드 | 사이트명 | URL | 설명 |
|----------|---------|-----|------|
| `eu_rohs` | EU RoHS 공식 사이트 | `https://ec.europa.eu/environment/waste/rohs_eee/index_en.htm` | 유럽연합 RoHS 규제 공식 정보 |
| `china_rohs` | 중국 RoHS 공식 사이트 | `https://www.china-rohs.org/` | 중국 RoHS 인증 및 규제 정보 |
| `japan_jmoss` | 일본 J-MOSS 사이트 | `https://www.j-moss.com/` | 일본 화학물질 정보 공개 사이트 |
| `korea_rohs` | 한국 법제처 | `https://www.law.go.kr/` | 한국 법령 정보 제공 사이트 |

**참고:**
- 각 사이트는 공식 기관에서 운영하며, RoHS 관련 최신 규제 정보를 제공합니다.
- 사이트 접근성에 따라 일부 소스는 일시적으로 사용할 수 없을 수 있습니다.
- 모든 데이터는 신뢰성 점수와 함께 검증됩니다.

### 웹 검색을 통한 업데이트 확인

RoHS 관련 최신 뉴스와 업데이트를 검색:

```bash
# RoHS 업데이트 검색
python scripts/rohs_etl.py --action web-search --query "RoHS regulation updates 2024" --max-results 10

# 중국 RoHS 변경사항 검색
python scripts/rohs_etl.py --action web-search --query "China RoHS phthalates 2026" --max-results 5
```

### RSS 피드 모니터링

공식 기관의 RSS 피드를 통해 규제 업데이트 모니터링:

```bash
python scripts/rohs_etl.py --action rss-monitor
```

### 웹 데이터 신뢰성 점수

각 웹 소스마다 신뢰성 점수가 부여됩니다:

- **EU 공식 사이트**: 0.95 (매우 높음)
- **중국 RoHS**: 0.90 (높음)
- **한국 법제처**: 0.92 (높음)
- **일본 J-MOSS**: 0.88 (높음)
- **웹 검색 결과**: 0.70 (중간)
- **RSS 피드**: 0.85 (높음)

### 주의사항

- **법적 제한**: 일부 웹사이트는 스크래핑을 허용하지 않을 수 있습니다. 공식 API 사용을 권장합니다.
- **속도 제한**: 과도한 요청은 IP 차단을 유발할 수 있습니다.
- **데이터 정확성**: 웹 데이터는 수동 검증 후 사용하세요.
- **캐싱**: 동일한 요청에 대해서는 로컬 캐시를 사용합니다.

### 고급 웹 데이터 수집

#### Python API 사용

```python
from scripts.rohs_etl import WebDataFetcher

fetcher = WebDataFetcher()

# 모든 소스에서 데이터 가져오기
all_data = fetcher.fetch_all_sources()

# 특정 소스에서만 가져오기
eu_data = fetcher._fetch_from_source(fetcher.data_sources['eu_rohs'])

# 웹 검색 수행
search_results = fetcher.search_web_for_updates("RoHS China 2026", 5)

# RSS 모니터링
rss_updates = fetcher.monitor_rss_feeds()
```

#### 데이터 소스 확장

새로운 웹 소스를 추가하려면 `WebDataFetcher.data_sources`에 항목을 추가하세요:

```python
new_source = {
    'url': 'https://example.com/rohs',
    'parser': self._parse_custom_source,
    'reliability': 0.80
}
self.data_sources['custom_rohs'] = new_source
```

## 수동 업데이트 방법

### 1. 명령줄 인터페이스 (CLI)

특정 국가의 특정 물질 제한 상태 업데이트:

```bash
python scripts/rohs_etl.py --action update --update data/json/rohs_compliance_data_20250101.json --country CN --substance DEHP --restricted true
```

데이터 요약 보기:

```bash
python scripts/rohs_etl.py --action summary --update data/json/rohs_compliance_data_20250101.json
```

### 2. Python API 사용

#### 기본 사용법

```python
from scripts.rohs_etl import ManualUpdater

# 업데이트할 JSON 파일 로드
updater = ManualUpdater('data/json/rohs_compliance_data_20250101.json')

# 중국의 DEHP 제한 상태를 True로 업데이트
updater.update_country_restriction('CN', 'DEHP', True)

# 변경사항 저장
updater.save_data()
```

#### 새로운 국가 추가

```python
# 새로운 국가 추가
restrictions = {
    'Pb': True, 'Hg': True, 'Cd': True, 'Cr6+': True,
    'PBB': False, 'PBDE': False, 'DEHP': False, 'BBP': False,
    'DBP': False, 'DIBP': False
}

updater.add_country(
    country_code='NZ',
    country_name='New Zealand',
    regulation='New Zealand RoHS',
    restrictions=restrictions,
    notes='Similar to EU regulations'
)

updater.save_data()
```

#### 국가 정보 조회

```python
# 특정 국가 정보 조회
china_info = updater.get_country_info('CN')
print(china_info)

# 모든 국가 코드 목록
countries = updater.list_countries()
print(countries)
```

#### 노트 업데이트

```python
# 국가 노트 업데이트
updater.update_country_notes('CN', 'Updated regulation effective from 2026')
updater.save_data()
```

#### 데이터 요약

```python
# 전체 데이터 요약
summary = updater.get_summary()
print(f"Total countries: {summary['total_countries']}")
print(f"Tracked substances: {summary['substances']}")

# 물질별 제한 현황
for substance, counts in summary['countries_by_restriction'].items():
    print(f"{substance}: {counts['restricted']} countries restrict it")
```

## 데이터 검증

### 자동 검증

ETL 프로세스 중 자동으로 수행되는 검증:

```bash
# ETL 실행 시 자동 검증
python scripts/rohs_etl.py
```

### 수동 검증

```python
from scripts.rohs_etl import RoHSEtlProcessor

processor = RoHSEtlProcessor()
# JSON 파일 로드 및 검증
with open('data/json/rohs_data.json', 'r') as f:
    data = json.load(f)

is_valid = processor.validate_data(data)
print(f"Data is valid: {is_valid}")
```

### 검증 규칙

1. **메타데이터 검증**: 필수 필드 존재 여부
2. **국가 데이터 검증**: 각 국가의 필수 필드 존재 여부
3. **제한 데이터 검증**: 모든 물질에 대한 제한 정보 존재 여부
4. **데이터 타입 검증**: 예상된 데이터 타입 일치 여부

## API 사용 예제

### ETL 프로세스 자동화

```python
from scripts.rohs_etl import RoHSEtlProcessor

# ETL 프로세서 초기화
processor = RoHSEtlProcessor()

# 데이터 추출 (수동 데이터 사용)
countries_data = processor.extract_from_manual_data()

# 데이터 변환
json_data = processor.transform_data(countries_data)

# 데이터 검증
if processor.validate_data(json_data):
    # JSON 파일로 저장
    output_file = processor.load_to_json(json_data)
    print(f"ETL completed: {output_file}")
```

### 대량 업데이트 스크립트

```python
from scripts.rohs_etl import ManualUpdater

def bulk_update_restrictions(json_file, updates):
    """
    여러 제한 사항을 한 번에 업데이트

    Args:
        json_file: JSON 파일 경로
        updates: 업데이트 목록 [(country, substance, restricted), ...]
    """
    updater = ManualUpdater(json_file)

    for country, substance, restricted in updates:
        try:
            updater.update_country_restriction(country, substance, restricted)
            print(f"Updated {country} {substance} to {restricted}")
        except ValueError as e:
            print(f"Error updating {country} {substance}: {e}")

    updater.save_data()
    print("Bulk update completed")

# 사용 예제
updates = [
    ('CN', 'DEHP', True),
    ('CN', 'BBP', True),
    ('CN', 'DBP', True),
    ('CN', 'DIBP', True),
    ('IN', 'DEHP', True),
]

bulk_update_restrictions('data/json/rohs_data.json', updates)
```

### 보고서 생성

```python
import json
from scripts.rohs_etl import ManualUpdater

def generate_compliance_report(json_file, output_file):
    """컴플라이언스 보고서 생성"""
    updater = ManualUpdater(json_file)
    summary = updater.get_summary()

    report = f"""
# RoHS Compliance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Countries: {summary['total_countries']}
- Substances Tracked: {', '.join(summary['substances'])}

## Restriction Statistics

| Substance | Restricted | Not Restricted | Unknown |
|-----------|------------|----------------|---------|
"""

    for substance, counts in summary['countries_by_restriction'].items():
        report += f"| {substance} | {counts['restricted']} | {counts['not_restricted']} | {counts['unknown']} |\n"

    report += "\n## Country Details\n\n"

    for country_code in updater.list_countries():
        country_info = updater.get_country_info(country_code)
        report += f"### {country_info['name']} ({country_code})\n"
        report += f"- Regulation: {country_info['regulation']}\n"
        report += f"- Notes: {country_info['notes']}\n"
        report += f"- Last Updated: {country_info['last_updated']}\n\n"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report generated: {output_file}")

# 사용 예제
generate_compliance_report(
    'data/json/rohs_data.json',
    'docs/rohs_compliance_report.md'
)
```

### 웹 데이터 수집 자동화

```python
from scripts.rohs_etl import WebDataFetcher, RoHSEtlProcessor

def automated_web_etl():
    """웹 데이터를 포함한 자동화된 ETL 프로세스"""
    # 웹 데이터 수집
    fetcher = WebDataFetcher()
    web_data = fetcher.fetch_all_sources()

    # ETL 프로세서로 웹 데이터와 기존 데이터 결합
    processor = RoHSEtlProcessor()

    # 웹 데이터를 포함한 ETL 실행
    processor.run_etl(include_web_data=True)

    print(f"Fetched {len(web_data)} records from web sources and processed into ETL")

# 실행
automated_web_etl()
```

### 실시간 모니터링 스크립트

```python
import time
import schedule
from scripts.rohs_etl import WebDataFetcher

def monitor_rohs_updates():
    """RoHS 업데이트를 정기적으로 모니터링"""
    fetcher = WebDataFetcher()

    # RSS 피드 모니터링
    rss_updates = fetcher.monitor_rss_feeds()
    if rss_updates:
        print(f"Found {len(rss_updates)} RSS updates:")
        for update in rss_updates:
            print(f"- {update['title']} ({update['published']})")

    # 웹 검색으로 최신 뉴스 확인
    search_results = fetcher.search_web_for_updates(
        "RoHS regulation changes 2024",
        max_results=3
    )
    if search_results:
        print(f"Found {len(search_results)} web search results:")
        for result in search_results:
            print(f"- {result['title']}")

# 매일 오전 9시에 실행
schedule.every().day.at("09:00").do(monitor_rohs_updates)

# 즉시 실행
monitor_rohs_updates()

# 스케줄러 실행 (실제 운영 시에는 백그라운드에서 실행)
# while True:
#     schedule.run_pending()
#     time.sleep(60)
```

### 데이터 소스 비교 및 검증

```python
from scripts.rohs_etl import WebDataFetcher, ManualUpdater

def compare_data_sources(json_file):
    """웹 데이터와 기존 데이터를 비교하여 불일치 검증"""
    updater = ManualUpdater(json_file)
    fetcher = WebDataFetcher()

    # 웹에서 최신 데이터 가져오기
    web_data = fetcher.fetch_all_sources()

    # 기존 데이터와 비교
    discrepancies = []
    for web_item in web_data:
        country_code = web_item['country_code']
        if country_code in updater.data['countries']:
            existing = updater.data['countries'][country_code]
            web_restrictions = web_item['restrictions']

            # 제한 사항 비교
            for substance, web_value in web_restrictions.items():
                existing_value = existing['restrictions'].get(substance)
                if web_value != existing_value and web_value is not None:
                    discrepancies.append({
                        'country': country_code,
                        'substance': substance,
                        'existing': existing_value,
                        'web': web_value,
                        'reliability': web_item.get('reliability', 0)
                    })

    # 신뢰성 높은 불일치만 보고
    high_reliability_discrepancies = [
        d for d in discrepancies if d['reliability'] >= 0.85
    ]

    if high_reliability_discrepancies:
        print("High-reliability data discrepancies found:")
        for disc in high_reliability_discrepancies:
            print(f"- {disc['country']} {disc['substance']}: "
                  f"Existing={disc['existing']}, Web={disc['web']} "
                  f"(Reliability: {disc['reliability']})")
    else:
        print("No significant discrepancies found.")

# 사용 예제
compare_data_sources('data/json/rohs_data.json')
```
```

## 문제 해결

### 일반적인 문제

#### 1. 파일을 찾을 수 없음

```
Error: CSV file not found: data/rohs_matrix.csv
```

**해결책**: 파일 경로를 확인하거나 수동 데이터 모드로 실행

```bash
python scripts/rohs_etl.py  # CSV 없이 실행
```

#### 2. 권한 오류

```
Error: Permission denied when writing to file
```

**해결책**: 디렉토리 권한 확인 및 수정

```bash
chmod 755 data/json/
```

#### 3. 데이터 검증 실패

```
Error: Data validation failed
```

**해결책**: 로그 메시지를 확인하여 누락된 필드나 잘못된 데이터 타입 식별

#### 4. 메모리 부족

대용량 CSV 파일 처리 시 메모리 부족이 발생할 수 있습니다.

**해결책**: 데이터를 청크 단위로 처리하도록 스크립트 수정

### 로그 확인

모든 작업은 `logs/` 디렉토리에 로그 파일이 생성됩니다:

```bash
tail -f logs/rohs_etl.log
```

### 디버그 모드

상세한 로깅을 위해 환경 변수 설정:

```bash
export LOG_LEVEL=DEBUG
python scripts/rohs_etl.py
```

## 버전 관리

### 버전 번호 매기기

- **주 버전**: 데이터 구조 변경 시 (예: 1.x → 2.x)
- **부 버전**: 새로운 기능 추가 시 (예: 1.1 → 1.2)
- **패치 버전**: 버그 수정 시 (예: 1.1.0 → 1.1.1)

### 버전 호환성

- 메이저 버전 변경: 기존 JSON 파일을 새 구조로 마이그레이션 필요
- 마이너 버전 변경: 하위 호환성 유지
- 패치 버전 변경: 완전 하위 호환성

### 백업 및 롤백

중요한 업데이트 전 항상 백업:

```bash
cp data/json/rohs_data.json data/json/rohs_data_backup.json
```

롤백 필요 시:

```bash
cp data/json/rohs_data_backup.json data/json/rohs_data.json
```

### 변경 로그

버전별 변경사항을 기록하는 `CHANGELOG.md` 파일 유지:

```markdown
# Changelog

## [1.1.0] - 2025-01-15
### Added
- New country: New Zealand
- Enhanced validation for restriction data

### Fixed
- Corrected Vietnam regulation name

## [1.0.0] - 2025-01-01
### Added
- Initial ETL functionality
- Manual update API
- Comprehensive user guide
```

## 지원 및 문의

문제가 발생하거나 추가 기능이 필요한 경우:

1. 로그 파일을 확인하여 오류 메시지 수집
2. 이 문서의 문제 해결 섹션 참고
3. 필요한 경우 개발팀에 문의

---

**문서 버전**: 1.0
**최종 업데이트**: 2025-01-01
**작성자**: AI Assistant
