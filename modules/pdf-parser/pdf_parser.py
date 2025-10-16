"""
PDF 파서 모듈 - 법령정보시스템 PDF에서 화학물질 데이터 추출

이 모듈은 산업안전보건법 관련 PDF 문서에서 화학물질 정보를 추출하여
구조화된 JSON 데이터로 변환합니다.

대상 문서:
1. 작업환경측정 대상 유해인자 (제186조제1항 관련)
2. 산업안전보건기준에 관한 규칙 [별표 12] 관리대상 유해물질

실행 방법:
    python modules/pdf-parser/pdf_parser.py --url <pdf_url> --output <output_file>
"""

import requests
import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

# PDF 처리 라이브러리들 (필요시 설치)
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import tabula
    HAS_TABULA = True
except ImportError:
    HAS_TABULA = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import camelot
    HAS_CAMELOT = True
except ImportError:
    HAS_CAMELOT = False

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PDFChemicalParser:
    """
    PDF에서 화학물질 정보를 추출하는 클래스
    """

    def __init__(self, download_dir: str = "data/pdfs"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

        # PDF 라이브러리 사용 가능 여부 확인
        self.available_libraries = {
            'pdfplumber': HAS_PDFPLUMBER,
            'tabula': HAS_TABULA,
            'PyPDF2': HAS_PYPDF2,
            'camelot': HAS_CAMELOT
        }

        logger.info(f"Available PDF libraries: {self.available_libraries}")

    def download_pdf(self, url: str, filename: Optional[str] = None) -> Path:
        """
        PDF 파일을 다운로드합니다.

        Args:
            url: PDF 파일 URL
            filename: 저장할 파일명 (없으면 URL에서 추출)

        Returns:
            다운로드된 파일 경로
        """
        if not filename:
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename.endswith('.pdf'):
                filename += '.pdf'

        filepath = self.download_dir / filename

        logger.info(f"Downloading PDF from: {url}")
        logger.info(f"Saving to: {filepath}")

        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"PDF download completed: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"PDF download failed: {e}")
            raise

    def extract_tables_pdfplumber(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        pdfplumber를 사용하여 PDF에서 표를 추출합니다.
        """
        if not HAS_PDFPLUMBER:
            raise ImportError("pdfplumber is not installed")

        tables_data = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                logger.info(f"Processing page {page_num + 1}")

                # 표 추출
                tables = page.extract_tables()

                for table_idx, table in enumerate(tables):
                    if not table:
                        continue

                    # 표 데이터를 구조화
                    headers = table[0] if len(table) > 0 else []
                    rows = table[1:] if len(table) > 1 else []

                    # 화학물질 데이터로 변환
                    chemicals = self._process_table_data(headers, rows, page_num, table_idx)
                    tables_data.extend(chemicals)

        return tables_data

    def extract_tables_tabula(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        tabula를 사용하여 PDF에서 표를 추출합니다.
        """
        if not HAS_TABULA:
            raise ImportError("tabula-py is not installed")

        # tabula로 모든 페이지의 표 추출
        try:
            tables = tabula.read_pdf(str(pdf_path), pages='all', multiple_tables=True)

            all_chemicals = []
            for table_idx, df in enumerate(tables):
                if df.empty:
                    continue

                # DataFrame을 리스트로 변환
                headers = df.columns.tolist()
                rows = df.values.tolist()

                chemicals = self._process_table_data(headers, rows, table_idx, 0)
                all_chemicals.extend(chemicals)

            return all_chemicals

        except Exception as e:
            logger.error(f"Tabula extraction failed: {e}")
            return []

    def _process_table_data(self, headers: List[str], rows: List[List],
                           page_num: int, table_num: int) -> List[Dict[str, Any]]:
        """
        추출된 표 데이터를 화학물질 정보로 변환합니다.
        """
        chemicals = []

        # 헤더 정리 (한글로 변환)
        clean_headers = [self._clean_header(header) for header in headers]

        for row_idx, row in enumerate(rows):
            if not row or all(not cell or str(cell).strip() == '' for cell in row):
                continue

            chemical_data = {
                'source_page': page_num + 1,
                'source_table': table_num + 1,
                'source_row': row_idx + 1,
                'raw_data': dict(zip(clean_headers, row))
            }

            # 구조화된 데이터 추출
            structured_data = self._extract_chemical_info(row, clean_headers)
            chemical_data.update(structured_data)

            chemicals.append(chemical_data)

        return chemicals

    def _clean_header(self, header: str) -> str:
        """헤더 텍스트를 정리합니다."""
        if not header:
            return ""

        # 문자열로 변환 및 정리
        header = str(header).strip()

        # 한글 헤더 매핑
        header_mapping = {
            '물질명': '물질명',
            '유해물질': '물질명',
            '화학물질명': '물질명',
            '명칭': '물질명',
            '이름': '물질명',

            'cas': 'CAS_No',
            'cas no': 'CAS_No',
            'cas_no': 'CAS_No',
            'cas번호': 'CAS_No',

            '관리등급': '관리등급',
            '등급': '관리등급',
            '위험등급': '관리등급',

            '특별관리': '특별관리물질',
            '특별관리물질': '특별관리물질',
            '관리대상': '관리대상',

            '비고': '비고',
            'remarks': '비고'
        }

        # 대소문자 통일 및 매핑
        header_lower = header.lower()
        for key, value in header_mapping.items():
            if key.lower() in header_lower:
                return value

        return header

    def _extract_chemical_info(self, row: List, headers: List[str]) -> Dict[str, Any]:
        """
        행 데이터에서 화학물질 정보를 추출합니다.
        """
        info = {}

        # 각 컬럼별로 데이터 추출
        for i, header in enumerate(headers):
            if i >= len(row):
                continue

            value = row[i]
            if not value or str(value).strip() in ['-', '', 'N/A']:
                continue

            value_str = str(value).strip()

            # 물질명 추출
            if header == '물질명':
                info['substance_name'] = value_str
                info['substance_name_korean'] = value_str

            # CAS 번호 추출
            elif header == 'CAS_No':
                cas_match = re.search(r'\d{1,7}-\d{2}-\d{1,2}', value_str)
                if cas_match:
                    info['cas_number'] = cas_match.group()
                else:
                    info['cas_number'] = value_str

            # 관리등급 추출
            elif header == '관리등급':
                info['management_grade'] = value_str

            # 특별관리물질 여부
            elif header == '특별관리물질':
                info['is_special_management'] = self._is_special_management(value_str)

            # 기타 정보
            else:
                info[header.lower().replace(' ', '_')] = value_str

        return info

    def _is_special_management(self, value: str) -> bool:
        """
        특별관리물질 여부를 판단합니다.
        """
        if not value:
            return False

        value_lower = str(value).lower()

        # 특별관리물질 표시 키워드
        special_keywords = [
            '특별관리',
            'special management',
            '특별',
            'special',
            '○',  # 동그라미 표시
            '●',  # 검은 동그라미
            'yes',
            'true',
            '1'
        ]

        return any(keyword in value_lower for keyword in special_keywords)

    def parse_pdf(self, pdf_url: str, method: str = 'auto') -> Dict[str, Any]:
        """
        PDF를 파싱하여 화학물질 데이터를 추출합니다.

        Args:
            pdf_url: PDF 파일 URL
            method: 추출 방법 ('auto', 'pdfplumber', 'tabula', 'camelot')

        Returns:
            추출된 데이터와 메타정보
        """
        logger.info(f"Starting PDF parsing: {pdf_url}")

        # PDF 다운로드
        pdf_path = self.download_pdf(pdf_url)

        # 추출 방법 선택
        if method == 'auto':
            # 사용 가능한 라이브러리 우선순위대로 시도
            methods = []
            if HAS_PDFPLUMBER:
                methods.append('pdfplumber')
            if HAS_TABULA:
                methods.append('tabula')
            if HAS_CAMELOT:
                methods.append('camelot')

            if not methods:
                raise ImportError("No PDF parsing libraries available. Install pdfplumber, tabula-py, or camelot-py.")

            method = methods[0]

        logger.info(f"Using extraction method: {method}")

        # 데이터 추출
        try:
            if method == 'pdfplumber':
                chemicals = self.extract_tables_pdfplumber(pdf_path)
            elif method == 'tabula':
                chemicals = self.extract_tables_tabula(pdf_path)
            elif method == 'camelot':
                # camelot 구현 (향후 추가)
                raise NotImplementedError("Camelot method not yet implemented")
            else:
                raise ValueError(f"Unsupported method: {method}")

            # 메타데이터 추가
            result = {
                'metadata': {
                    'source_url': pdf_url,
                    'local_file': str(pdf_path),
                    'extraction_method': method,
                    'total_chemicals': len(chemicals),
                    'extraction_timestamp': str(pd.Timestamp.now())
                },
                'data': chemicals
            }

            logger.info(f"PDF parsing completed. Extracted {len(chemicals)} chemical records.")
            return result

        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            raise

def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='PDF 화학물질 데이터 추출기')
    parser.add_argument('--url', required=True, help='PDF 파일 URL')
    parser.add_argument('--output', default='pdf_chemicals.json', help='출력 JSON 파일명')
    parser.add_argument('--method', choices=['auto', 'pdfplumber', 'tabula', 'camelot'],
                       default='auto', help='추출 방법')
    parser.add_argument('--data-dir', default='data', help='데이터 저장 디렉토리')

    args = parser.parse_args()

    # PDF 파서 초기화
    parser = PDFChemicalParser(download_dir=f"{args.data_dir}/pdfs")

    try:
        # PDF 파싱
        result = parser.parse_pdf(args.url, method=args.method)

        # 결과 저장
        output_path = Path(args.data_dir) / args.output
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Total chemicals extracted: {result['metadata']['total_chemicals']}")

    except Exception as e:
        logger.error(f"PDF parsing failed: {e}")
        raise

if __name__ == "__main__":
    main()
