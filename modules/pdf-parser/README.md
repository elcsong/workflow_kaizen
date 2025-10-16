# PDF 화학물질 데이터 추출 모듈

법령정보시스템 PDF 문서에서 화학물질 정보를 자동으로 추출하여 구조화된 JSON 데이터로 변환하는 모듈입니다.

## 📋 개요

현재 법령정보시스템 화재로 인한 접근 불가 상황에서, 시스템 복구 후 PDF 문서를 효과적으로 파싱하기 위한 모듈입니다.

## 🎯 대상 문서

### 1. 작업환경측정 대상 유해인자
- **법령**: 산업안전보건법 제186조제1항
- **내용**: 작업장 유해인자 측정 대상 물질 목록
- **형식**: 표 형식의 PDF 문서

### 2. 산업안전보건기준에 관한 규칙 [별표 12]
- **법령**: 산업안전보건기준에 관한 규칙
- **내용**: 관리대상 유해물질의 종류 및 기준
- **형식**: 표 형식의 PDF 문서

## 🛠️ 기술 스택

### PDF 처리 라이브러리
- **pdfplumber**: 텍스트 및 표 추출에 최적화
- **tabula-py**: 복잡한 표 구조 처리에 강력
- **PyPDF2**: 기본적인 PDF 텍스트 추출
- **camelot-py**: 고급 표 추출 (OpenCV 기반)

### 데이터 처리
- **pandas**: 표 데이터 구조화
- **regex**: CAS 번호 패턴 매칭
- **json**: 구조화된 데이터 저장

## 📊 추출 데이터 구조

```json
{
  "metadata": {
    "source_url": "https://law.go.kr/xxx.pdf",
    "local_file": "data/pdfs/law_document.pdf",
    "extraction_method": "pdfplumber",
    "total_chemicals": 150,
    "extraction_timestamp": "2025-01-15T10:30:00"
  },
  "data": [
    {
      "source_page": 1,
      "source_table": 1,
      "source_row": 1,
      "substance_name": "벤젠",
      "substance_name_korean": "벤젠",
      "cas_number": "71-43-2",
      "management_grade": "1급",
      "is_special_management": true,
      "raw_data": {
        "물질명": "벤젠",
        "CAS번호": "71-43-2",
        "관리등급": "1급",
        "특별관리": "○"
      }
    }
  ]
}
```

## 🚀 사용 방법

### 기본 사용법
```bash
# PDF URL에서 데이터 추출
python modules/pdf-parser/pdf_parser.py \
  --url "https://law.go.kr/download/chemical_list.pdf" \
  --output "chemical_data.json"
```

### 고급 옵션
```bash
# 특정 추출 방법 지정
python modules/pdf-parser/pdf_parser.py \
  --url "https://law.go.kr/download/chemical_list.pdf" \
  --method "tabula" \
  --output "chemical_data_tabula.json" \
  --data-dir "data"
```

### Python 코드에서 사용
```python
from modules.pdf_parser.pdf_parser import PDFChemicalParser

# 파서 초기화
parser = PDFChemicalParser()

# PDF 파싱
result = parser.parse_pdf(
    pdf_url="https://law.go.kr/download/chemical_list.pdf",
    method="pdfplumber"
)

# 결과 저장
with open('chemical_data.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"추출된 화학물질: {result['metadata']['total_chemicals']}개")
```

## 🔍 추출 로직 상세

### 1. PDF 다운로드
- URL에서 PDF 파일 자동 다운로드
- `data/pdfs/` 디렉토리에 저장
- 파일명 자동 생성 또는 지정 가능

### 2. 표 추출
- **pdfplumber**: 페이지별 표 탐색 및 추출
- **tabula**: Java 기반 고정밀도 표 추출
- **camelot**: 이미지 기반 복합 표 처리

### 3. 데이터 정제
- **헤더 인식**: 한글/영문 헤더 자동 매핑
- **CAS 번호 추출**: 정규식 패턴 매칭 (`\d{1,7}-\d{2}-\d{1,2}`)
- **특별관리물질 판별**: 키워드 기반 분류

### 4. 구조화
- 원본 데이터 보존 (`raw_data`)
- 표준화된 필드명 적용
- 메타데이터 추가 (출처, 타임스탬프 등)

## 📋 필드 설명

| 필드명 | 설명 | 예시 |
|--------|------|------|
| `substance_name` | 화학물질 영문명 | "Benzene" |
| `substance_name_korean` | 화학물질 한글명 | "벤젠" |
| `cas_number` | CAS 등록번호 | "71-43-2" |
| `management_grade` | 관리 등급 | "1급", "2급" |
| `is_special_management` | 특별관리물질 여부 | true/false |
| `source_page` | PDF 페이지 번호 | 1 |
| `source_table` | 페이지 내 표 번호 | 1 |
| `source_row` | 표 내 행 번호 | 5 |

## ⚙️ 설치 및 설정

### 필수 라이브러리 설치
```bash
pip install pdfplumber tabula-py PyPDF2 camelot-py[cv]
```

### Java 의존성 (tabula용)
```bash
# macOS
brew install openjdk

# Ubuntu/Debian
sudo apt-get install default-jre

# Windows: 자동으로 설치됨
```

### OpenCV 의존성 (camelot용)
```bash
# macOS
brew install opencv

# Ubuntu/Debian
sudo apt-get install python3-opencv

# Windows
pip install opencv-python
```

## 🔧 문제 해결

### PDF 추출 실패 시
1. **다른 라이브러리 시도**:
   ```bash
   # pdfplumber 실패 시 tabula 시도
   python pdf_parser.py --method tabula --url <pdf_url>
   ```

2. **PDF 품질 확인**:
   - 스캔된 PDF의 경우 camelot 권장
   - 텍스트 기반 PDF의 경우 pdfplumber 권장

3. **표 구조 확인**:
   - 복잡한 병합 셀은 수동 전처리 필요
   - 규칙적인 표 구조 선호

### 데이터 정확도 향상
- **헤더 매핑 개선**: `_clean_header()` 메서드 확장
- **CAS 번호 패턴**: 다양한 포맷 지원 추가
- **특별관리물질 판별**: 키워드 확장

## 🔗 통합 계획

### 기존 ETL 파이프라인 연동
```python
# KOSHA ETL 모듈에 PDF 파서 통합
from modules.pdf_parser.pdf_parser import PDFChemicalParser

class EnhancedKOSHAETL:
    def __init__(self):
        self.pdf_parser = PDFChemicalParser()

    def extract_from_pdf_sources(self):
        # 법령정보시스템 PDF에서 데이터 추출
        pdf_urls = [
            "https://law.go.kr/제186조_유해인자.pdf",
            "https://law.go.kr/별표12_유해물질.pdf"
        ]

        all_data = []
        for url in pdf_urls:
            try:
                result = self.pdf_parser.parse_pdf(url)
                all_data.extend(result['data'])
            except Exception as e:
                logger.error(f"PDF extraction failed for {url}: {e}")

        return all_data
```

### 대시보드 통합
- PDF 파싱 결과를 기존 KOSHA 대시보드에 통합
- 데이터 출처 구분 (웹 vs PDF)
- 비교 분석 기능 추가

## 📈 향후 개선 방향

### 단기 개선
- [ ] 다양한 PDF 포맷 지원 확장
- [ ] 표 병합/분할 자동 처리
- [ ] 다국어 텍스트 처리 개선

### 장기 발전
- [ ] 머신러닝 기반 표 인식
- [ ] OCR 기능 추가 (이미지 기반 PDF)
- [ ] 자동화된 PDF 업데이트 모니터링
- [ ] 법령 개정 자동 감지

## 📞 문의 및 기여

법령정보시스템 복구 후 PDF 파싱 테스트 및 개선에 참여하고 싶으시면 이슈를 남겨주세요!

---

**⚠️ 참고**: 현재 법령정보시스템 화재로 인한 접근 불가 상태입니다. 시스템 복구 후 실제 PDF URL로 테스트 예정입니다.
