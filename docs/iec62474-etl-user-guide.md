# IEC62474 ETL 사용자 가이드

## 목차
1. [개요](#개요)
2. [설치 및 요구사항](#설치-및-요구사항)
3. [빠른 시작](#빠른-시작)
4. [상세 사용법](#상세-사용법)
5. [데이터 구조](#데이터-구조)
6. [FAQ](#faq)
7. [문제 해결](#문제-해결)

---

## 개요

IEC62474 ETL 시스템은 전기전자 산업을 위한 국제 표준 물질 선언 데이터베이스인 IEC62474 Declarable Substances List를 자동으로 수집하고 처리하는 도구입니다.

### 주요 특징
- ✅ **통합 규제 관리**: RoHS, REACH, GADSL, Conflict Minerals, TSCA, POPs 등 다양한 규제 통합
- ✅ **자동 데이터 수집**: IEC62474 공식 웹사이트에서 최신 데이터 자동 다운로드
- ✅ **구조화된 JSON 출력**: 분석 및 활용이 용이한 JSON 형식
- ✅ **항상 최신 유지**: 고정된 파일명으로 항상 최신 버전만 유지
- ✅ **400개 이상 물질**: 전 세계 규제 물질 종합 관리

### 포함된 규제
| 규제 | 설명 | 적용 지역 |
|------|------|-----------|
| **RoHS** | Restriction of Hazardous Substances | EU, 전 세계 |
| **REACH** | SVHC, Annex XIV, Annex XVII | EU |
| **GADSL** | Global Automotive Declarable Substance List | 자동차 산업 |
| **Conflict Minerals** | 분쟁 광물 (3TG) | 미국 |
| **TSCA** | Toxic Substances Control Act | 미국 |
| **POPs** | Persistent Organic Pollutants | EU, 국제 |

---

## 설치 및 요구사항

### 시스템 요구사항
- **운영체제**: Windows, macOS, Linux
- **Python**: 3.9 이상
- **브라우저**: Chrome 또는 Edge (자동 설치됨)
- **네트워크**: 인터넷 연결 필요 (데이터 다운로드 시)

### 필수 패키지 설치
```bash
# 가상환경 활성화 (프로젝트 루트에서)
source kaizen-venv/bin/activate  # Linux/macOS
# 또는
kaizen-venv\Scripts\activate  # Windows

# 필요한 패키지 확인
pip install selenium webdriver-manager
```

---

## 빠른 시작

### 1. 최신 데이터 수집 (권장)
```bash
cd /path/to/win_workflow_kaizen
python modules/etl-pipeline/iec62474_etl.py
```

**실행 결과:**
- IEC62474 웹사이트에서 최신 XML 다운로드
- 자동 파싱 및 변환
- `data/iec62474_substances.json` 생성 (기존 파일 덮어쓰기)

### 2. 기존 데이터 사용
```bash
# 이미 다운로드한 XML 파일이 있는 경우
python modules/etl-pipeline/iec62474_etl.py --skip-download
```

---

## 상세 사용법

### 명령줄 옵션

```bash
usage: iec62474_etl.py [-h] [--skip-download] [--xml-file XML_FILE] [--data-dir DATA_DIR]

options:
  -h, --help            도움말 표시
  --skip-download       다운로드 생략, 기존 XML 파일 사용
  --xml-file XML_FILE   사용할 XML 파일 경로 지정
  --data-dir DATA_DIR   데이터 디렉토리 (기본값: data)
```

### 실행 예제

#### 예제 1: 일반 실행 (최신 데이터 다운로드)
```bash
python modules/etl-pipeline/iec62474_etl.py
```

**출력:**
```
2025-10-27 22:10:06 - INFO - Starting IEC62474 ETL process...
2025-10-27 22:10:06 - INFO - Successfully downloaded XML
2025-10-27 22:10:06 - INFO - Found 205 substance elements in XML
2025-10-27 22:10:06 - INFO - Parsed 138 substances from XML

============================================================
ETL Process Completed Successfully!
============================================================
Output file: data/iec62474_substances.json

The JSON file always contains the latest data.
Previous version has been replaced.
============================================================
```

#### 예제 2: 기존 XML 사용
```bash
python modules/etl-pipeline/iec62474_etl.py --skip-download
```

#### 예제 3: 특정 XML 파일 지정
```bash
python modules/etl-pipeline/iec62474_etl.py --skip-download \
  --xml-file data/downloads/IEC62474_DeclarableSubstances_vD31.00_2025-10-27.xml
```

---

## 데이터 구조

### JSON 출력 파일 구조

```json
{
  "metadata": {
    "version": "2.0",
    "standard": "IEC62474",
    "last_updated": "2025-10-27 22:10:06",
    "source": "https://std.iec.ch/iec62474",
    "total_substances": 138,
    "regulations": ["RoHS", "REACH", "GADSL", "TSCA", "POPs"],
    "description": "IEC62474 Declarable Substances List..."
  },
  "substances": [...],
  "substance_groups": {...}
}
```

### 물질 데이터 필드

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `id` | string | 물질 고유 ID | "00001" |
| `name` | string | 물질명 | "Diarsenic pentoxide" |
| `cas_number` | string | CAS 등록번호 | "1303-28-2" |
| `substance_group` | string | 물질 그룹 | "Heavy Metals" |
| `alternative_names` | array | 대체 이름 목록 | ["Lead", "Pb"] |
| `typical_applications` | string | 일반 응용 분야 | "Batteries, solder" |
| `reporting_threshold` | string | 보고 임계값 | "0.1 mass% of article" |
| `reporting_level` | string | 보고 레벨 | "Article", "Material", "Product" |
| `reporting_requirement` | string | 보고 요구사항 | "Mandatory", "Optional" |
| `regulations` | object | 적용 규제 목록 | {"RoHS": {...}, "REACH": {...}} |
| `basis_description` | string | 규제 근거 설명 | "[EU] REACH Regulation..." |
| `first_added` | string | 최초 추가일 | "2010-04-02" |
| `last_revised` | string | 최종 수정일 | "2025-03-15" |
| `comments` | string | 주석 및 변경 이력 | "Updated threshold..." |

### 규제 정보 구조

```json
"regulations": {
  "RoHS": {
    "source": "EU Directive 2011/65/EU"
  },
  "REACH": {
    "source": "EU Regulation (EC) No.1907/2006",
    "svhc": true,
    "annex_xvii": true,
    "annex_xiv": false
  }
}
```

---

## FAQ

### Q1: JSON 파일이 항상 덮어써지나요?
**A:** 네, 맞습니다. `iec62474_substances.json` 파일은 항상 최신 버전으로 덮어씁니다. 이전 버전을 보관하려면 수동으로 백업해야 합니다.

```bash
# 백업 예제
cp data/iec62474_substances.json \
   data/iec62474_substances_backup_$(date +%Y%m%d).json
```

### Q2: 얼마나 자주 업데이트해야 하나요?
**A:** IEC62474는 분기별로 업데이트됩니다. 월 1회 또는 분기별 실행을 권장합니다.

### Q3: 다운로드가 실패하면 어떻게 하나요?
**A:** 다음을 확인해보세요:
1. 인터넷 연결 상태
2. IEC62474 웹사이트 접근 가능 여부
3. 방화벽 설정
4. Chrome/Edge 브라우저 설치 여부

### Q4: 특정 규제의 물질만 필터링할 수 있나요?
**A:** JSON 파일 로드 후 프로그래밍으로 필터링 가능합니다:

```python
import json

# JSON 파일 로드
with open('data/iec62474_substances.json', 'r') as f:
    data = json.load(f)

# RoHS 관련 물질만 필터링
rohs_substances = [
    s for s in data['substances']
    if 'RoHS' in s.get('regulations', {})
]

print(f"Found {len(rohs_substances)} RoHS substances")
```

### Q5: REACH 데이터와 중복되지 않나요?
**A:** IEC62474는 REACH를 포함한 더 넓은 범위의 규제를 커버합니다. 두 데이터를 함께 사용하여 크로스 참조가 가능합니다.

---

## 문제 해결

### 문제 1: WebDriver 초기화 실패
```
Error: All WebDriver initializations failed
```

**해결방법:**
```bash
# WebDriver 재설치
pip install --upgrade selenium webdriver-manager

# 캐시 삭제
rm -rf ~/.wdm  # Linux/macOS
rmdir /s %USERPROFILE%\.wdm  # Windows
```

### 문제 2: XML 다운로드 타임아웃
```
Error: XML download did not complete within timeout
```

**해결방법:**
1. 인터넷 연결 확인
2. IEC62474 사이트가 점검 중인지 확인
3. 재시도 (네트워크 속도에 따라 시간이 걸릴 수 있음)

### 문제 3: 파싱 오류
```
Error: Error parsing XML
```

**해결방법:**
1. XML 파일이 완전히 다운로드되었는지 확인
2. XML 파일 크기 확인 (최소 1MB 이상)
3. 다시 다운로드 시도

### 문제 4: 물질 수가 예상보다 적음
```
INFO - Parsed 138 substances from XML
```

**참고:** 이는 정상입니다. XML에는 물질 그룹 참조가 포함되어 있으며, 실제 개별 물질만 파싱됩니다. 물질 그룹은 별도의 Reference Substance 워크시트에 정의되어 있습니다.

---

## 추가 리소스

### 관련 문서
- [ETL 모듈 설명서](../modules/etl-pipeline/ETL_Modules_Documentation.md)
- [IEC62474 공식 사이트](https://std.iec.ch/iec62474)

### 지원
- 문제 발생 시: GitHub Issues 또는 프로젝트 관리자에게 문의
- 데이터 업데이트: IEC62474 공식 사이트 참조

---

## 라이선스 및 법적 고지

이 ETL 도구는 공개된 IEC62474 데이터베이스를 수집하며, 데이터의 저작권은 IEC에 있습니다. 수집된 데이터는 규제 준수 목적으로만 사용해야 합니다.

**마지막 업데이트:** 2025-10-27

