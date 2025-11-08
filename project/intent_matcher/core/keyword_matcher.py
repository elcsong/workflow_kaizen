"""
키워드 기반 필터링 및 분석 매처
사용자 제공 키워드로 1차 필터링 후 2차 유사도 판별
"""
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
from datetime import datetime
import difflib
 
from .matcher import DefectMatcher
from ..extract.keywords import KeywordExtractor
 
class KeywordBasedMatcher:
    """키워드 기반 필터링 및 분석 매처"""
   
    def __init__(self,
                 keywords: str,
                 similarity_threshold: float = 0.9,
                 use_sbert: bool = True,
                 alpha: float = 0.5):
        """
        Args:
            keywords: 콤마로 구분된 필터링 키워드 (예: "blood,bleed,crystal")
            similarity_threshold: 유사 키워드 매칭 임계값
            use_sbert: SBERT 사용 여부
            alpha: 룰 vs 의미 점수 가중치
        """
        self.raw_keywords = keywords
        self.keywords = self._parse_keywords(keywords)
        self.similarity_threshold = similarity_threshold
        self.use_sbert = use_sbert
        self.alpha = alpha
       
        # 분석 설정 저장
        self.analysis_config = {
            'keywords': self.keywords,
            'similarity_threshold': similarity_threshold,
            'use_sbert': use_sbert,
            'alpha': alpha,
            'analysis_method': 'Keyword-Based Filtering + Semantic Analysis',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
       
        # 텍스트 컬럼 정의
        self.text_columns = [
            'Customers Issue Description(Full)',
            "FE's Issue Description(Full)",
            'Actions Taken / Repairs(Full)',
            'Repair Test / Inspection Data(Full)'
        ]
       
        logging.info(f"KeywordBasedMatcher initialized with keywords: {self.keywords}")
   
    def _parse_keywords(self, keywords_str: str) -> List[str]:
        """콤마로 구분된 키워드 문자열을 리스트로 변환"""
        if not keywords_str:
            return []
       
        keywords = [kw.strip().lower() for kw in keywords_str.split(',')]
        keywords = [kw for kw in keywords if kw]  # 빈 문자열 제거
       
        return keywords
   
    def _generate_keyword_variants(self, keyword: str) -> List[str]:
        """키워드의 다양한 변형 생성 (유사문자, 어간 변화 등)"""
        variants = [keyword]
       
        # 기본 대소문자 변형
        variants.extend([
            keyword.upper(),
            keyword.capitalize(),
            keyword.title()
        ])
       
        # 어간 변화 (간단한 패턴)
        if keyword.endswith('y'):
            variants.append(keyword[:-1] + 'ies')  # bleed -> bleedy
            variants.append(keyword + 'ing')      # bleed -> bleeding
       
        if not keyword.endswith('ing'):
            variants.append(keyword + 'ing')      # blood -> blooding
       
        if not keyword.endswith('ed'):
            variants.append(keyword + 'ed')       # blood -> blooded
       
        if not keyword.endswith('s'):
            variants.append(keyword + 's')        # crystal -> crystals
       
        # 복수형 변형
        if keyword.endswith('s') and len(keyword) > 2:
            variants.append(keyword[:-1])         # crystals -> crystal
       
        return list(set(variants))  # 중복 제거
   
    def _fuzzy_match_keyword(self, text: str, keyword: str) -> List[Tuple[str, float, int, int]]:
        """
        텍스트에서 키워드와 유사한 단어들을 찾기
       
        Returns:
            List of (matched_word, similarity_score, start_pos, end_pos)
        """
        if not text or not keyword:
            return []
       
        matches = []
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
       
        # 키워드 변형들 생성
        keyword_variants = self._generate_keyword_variants(keyword)
       
        for word in set(words):  # 중복 제거
            # 정확한 매치 확인
            if any(variant.lower() == word for variant in keyword_variants):
                # 원본 텍스트에서 위치 찾기
                pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                for match in pattern.finditer(text):
                    matches.append((match.group(), 1.0, match.start(), match.end()))
            else:
                # 유사도 매칭
                for variant in keyword_variants:
                    similarity = difflib.SequenceMatcher(None, word, variant.lower()).ratio()
                    if similarity >= self.similarity_threshold:
                        # 원본 텍스트에서 위치 찾기
                        pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
                        for match in pattern.finditer(text):
                            matches.append((match.group(), similarity, match.start(), match.end()))
       
        # 유사도 순으로 정렬
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
   
    def _filter_by_keywords(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """키워드로 데이터프레임 필터링"""
        filtered_indices = []
        keyword_evidence = {}
       
        for idx, row in df.iterrows():
            row_matches = {}
            total_matches = 0
           
            for col in self.text_columns:
                if col not in row or pd.isna(row[col]):
                    continue
               
                text = str(row[col])
                col_matches = []
               
                for keyword in self.keywords:
                    matches = self._fuzzy_match_keyword(text, keyword)
                    if matches:
                        col_matches.extend([(keyword, match) for match in matches])
                        total_matches += len(matches)
               
                if col_matches:
                    row_matches[col] = col_matches
           
            if total_matches > 0:
                filtered_indices.append(idx)
                keyword_evidence[idx] = row_matches
       
        filtered_df = df.loc[filtered_indices].copy() if filtered_indices else pd.DataFrame()
        evidence_df = pd.DataFrame.from_dict(keyword_evidence, orient='index')
       
        return filtered_df, evidence_df
   
    def _format_evidence(self, evidence_dict: Dict) -> str:
        """증거를 사람이 읽기 쉬운 형태로 포맷팅"""
        if not evidence_dict:
            return ""
       
        formatted_parts = []
       
        for col, matches in evidence_dict.items():
            if not matches:
                continue
           
            col_short = col.split('(')[0].strip()  # "Customers Issue Description(Full)" -> "Customers Issue Description"
            match_strs = []
           
            for keyword, (matched_word, similarity, start, end) in matches:
                if similarity >= 0.95:
                    match_strs.append(f'"{matched_word}"')
                else:
                    match_strs.append(f'"{matched_word}"({similarity:.2f})')
           
            if match_strs:
                formatted_parts.append(f"{col_short}: {', '.join(match_strs)}")
       
        return " | ".join(formatted_parts)
   
    def _create_settings_sheet_data(self) -> pd.DataFrame:
        """분석 설정 정보를 담은 데이터프레임 생성"""
        settings_data = []
       
        # 기본 설정
        settings_data.append({
            'Setting Category': 'Analysis Method',
            'Setting Name': 'Method',
            'Setting Value': self.analysis_config['analysis_method'],
            'Description': 'Primary analysis approach used'
        })
       
        settings_data.append({
            'Setting Category': 'Keywords',
            'Setting Name': 'Input Keywords',
            'Setting Value': self.raw_keywords,
            'Description': 'User-provided keywords for filtering'
        })
       
        settings_data.append({
            'Setting Category': 'Keywords',
            'Setting Name': 'Processed Keywords',
            'Setting Value': ', '.join(self.keywords),
            'Description': 'Processed and normalized keywords'
        })
       
        settings_data.append({
            'Setting Category': 'Filtering Parameters',
            'Setting Name': 'Similarity Threshold',
            'Setting Value': str(self.similarity_threshold),
            'Description': 'Minimum similarity score for fuzzy keyword matching'
        })
       
        settings_data.append({
            'Setting Category': 'Analysis Parameters',
            'Setting Name': 'Use SBERT',
            'Setting Value': str(self.use_sbert),
            'Description': 'Whether to use semantic analysis with SBERT'
        })
       
        settings_data.append({
            'Setting Category': 'Analysis Parameters',
            'Setting Name': 'Alpha (Rule Weight)',
            'Setting Value': str(self.alpha),
            'Description': 'Weight for rule-based vs semantic scoring (0.0-1.0)'
        })
       
        settings_data.append({
            'Setting Category': 'Text Columns',
            'Setting Name': 'Analyzed Columns',
            'Setting Value': ' | '.join(self.text_columns),
            'Description': 'Text columns used for analysis'
        })
       
        settings_data.append({
            'Setting Category': 'Execution Info',
            'Setting Name': 'Timestamp',
            'Setting Value': self.analysis_config['timestamp'],
            'Description': 'When this analysis was performed'
        })
       
        return pd.DataFrame(settings_data)
   
    def analyze_excel(self,
                     file_path: str,
                     sheet_name: str = 'Sheet1',
                     output_path: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        엑셀 파일 분석 수행
       
        Args:
            file_path: 엑셀 파일 경로
            sheet_name: 시트명
            output_path: 결과 저장 경로 (None이면 자동 생성)
           
        Returns:
            (결과 데이터프레임, 분석 요약 정보)
        """
        logging.info(f"Starting analysis of {file_path}")
       
        # 엑셀 파일 로드
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            logging.info(f"Loaded {len(df)} records from {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to load Excel file: {e}")
       
        # 필수 컬럼 확인
        missing_cols = [col for col in self.text_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
       
        # 1차: 키워드 필터링
        logging.info("Phase 1: Keyword filtering...")
        filtered_df, evidence_df = self._filter_by_keywords(df)
       
        if filtered_df.empty:
            logging.warning("No records matched the keywords")
            return pd.DataFrame(), {
                'total_records': len(df),
                'filtered_records': 0,
                'keywords_used': self.keywords
            }
       
        logging.info(f"Filtered to {len(filtered_df)} records ({len(filtered_df)/len(df)*100:.1f}%)")
       
        # 결과 데이터프레임 구성
        result_df = filtered_df.copy()
       
        # 키워드 매칭 정보 추가
        result_df['Keyword_Filter_Status'] = 'MATCHED'
        result_df['Keywords_Found'] = ''
        result_df['Match_Evidence'] = ''
        result_df['Match_Details'] = ''
       
        # 각 행에 대한 키워드 매칭 정보 추가
        for idx in result_df.index:
            if idx in evidence_df.index:
                evidence = evidence_df.loc[idx].to_dict()
               
                # 찾은 키워드들 수집
                found_keywords = set()
                match_details = []
               
                for col, matches in evidence.items():
                    if matches and isinstance(matches, list):
                        for keyword, (matched_word, similarity, start, end) in matches:
                            found_keywords.add(keyword)
                            match_details.append({
                                'column': col,
                                'keyword': keyword,
                                'matched_word': matched_word,
                                'similarity': similarity,
                                'position': (start, end)
                            })
               
                result_df.loc[idx, 'Keywords_Found'] = ', '.join(sorted(found_keywords))
                result_df.loc[idx, 'Match_Evidence'] = self._format_evidence(evidence)
               
                # 상세 매칭 정보 (JSON 형태로 저장)
                import json
                result_df.loc[idx, 'Match_Details'] = json.dumps(match_details, ensure_ascii=False)
       
        # 분석 요약 정보
        summary = {
            'total_records': len(df),
            'filtered_records': len(filtered_df),
            'filter_rate': len(filtered_df) / len(df) * 100,
            'keywords_used': self.keywords,
            'analysis_config': self.analysis_config
        }
       
        # 결과 저장
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            keywords_str = '_'.join(self.keywords[:3])  # 처음 3개 키워드만 사용
            output_path = f"keyword_analysis_{keywords_str}_{timestamp}.xlsx"
       
        # 설정 시트 데이터 생성
        settings_df = self._create_settings_sheet_data()
       
        # 엑셀 파일로 저장 (여러 시트)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 메인 결과 시트
            result_df.to_excel(writer, sheet_name='Analysis_Results', index=False)
           
            # 설정 정보 시트
            settings_df.to_excel(writer, sheet_name='Analysis_Settings', index=False)
           
            # 키워드 매칭 통계 시트
            keyword_stats = self._create_keyword_statistics(result_df)
            keyword_stats.to_excel(writer, sheet_name='Keyword_Statistics', index=False)
       
        logging.info(f"Results saved to {output_path}")
       
        return result_df, summary
   
    def _create_keyword_statistics(self, result_df: pd.DataFrame) -> pd.DataFrame:
        """키워드 매칭 통계 생성"""
        stats_data = []
       
        # 각 키워드별 통계
        for keyword in self.keywords:
            keyword_matches = 0
            column_matches = {col: 0 for col in self.text_columns}
           
            for idx, row in result_df.iterrows():
                keywords_found = str(row.get('Keywords_Found', '')).lower()
                if keyword in keywords_found:
                    keyword_matches += 1
               
                # 컬럼별 매칭 확인
                match_evidence = str(row.get('Match_Evidence', ''))
                for col in self.text_columns:
                    col_short = col.split('(')[0].strip()
                    if col_short in match_evidence and keyword in match_evidence.lower():
                        column_matches[col] += 1
           
            stats_data.append({
                'Keyword': keyword,
                'Total_Matches': keyword_matches,
                'Match_Rate': f"{keyword_matches/len(result_df)*100:.1f}%" if len(result_df) > 0 else "0%",
                'Customer_Column_Matches': column_matches[self.text_columns[0]],
                'FE_Column_Matches': column_matches[self.text_columns[1]],
                'Actions_Column_Matches': column_matches[self.text_columns[2]],
                'Test_Column_Matches': column_matches[self.text_columns[3]]
            })
       
        return pd.DataFrame(stats_data)
 
def main():
    """테스트용 메인 함수"""
    import argparse
   
    parser = argparse.ArgumentParser(description='Keyword-based filtering and analysis')
    parser.add_argument('--file', '-f', required=True, help='Excel file path')
    parser.add_argument('--keywords', '-k', required=True, help='Comma-separated keywords')
    parser.add_argument('--sheet', '-s', default='Sheet1', help='Sheet name')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--threshold', '-t', type=float, default=0.7, help='Similarity threshold')
    parser.add_argument('--use-sbert', action='store_true', help='Use SBERT analysis')
    parser.add_argument('--alpha', type=float, default=0.5, help='Rule vs semantic weight')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
   
    args = parser.parse_args()
   
    # 로깅 설정
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
   
    # 매처 생성 및 실행
    matcher = KeywordBasedMatcher(
        keywords=args.keywords,
        similarity_threshold=args.threshold,
        use_sbert=args.use_sbert,
        alpha=args.alpha
    )
   
    try:
        result_df, summary = matcher.analyze_excel(
            file_path=args.file,
            sheet_name=args.sheet,
            output_path=args.output
        )
       
        print(f"\n=== Analysis Summary ===")
        print(f"Total records: {summary['total_records']}")
        print(f"Filtered records: {summary['filtered_records']}")
        print(f"Filter rate: {summary['filter_rate']:.1f}%")
        print(f"Keywords used: {', '.join(summary['keywords_used'])}")
       
        if len(result_df) > 0:
            print(f"\n=== Top 5 Matches ===")
            for idx, row in result_df.head().iterrows():
                print(f"Row {idx}: {row['Keywords_Found']} | {row['Match_Evidence'][:100]}...")
       
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return 1
   
    return 0
 
if __name__ == '__main__':
    exit(main())