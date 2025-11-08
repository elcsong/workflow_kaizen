"""
키워드 추출 및 매칭 모듈
증상, 동의어, 조치, 부품 힌트 등을 텍스트에서 찾아내는 기능
"""
import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
 
@dataclass
class MatchSpan:
    """매칭된 텍스트 스팬 정보"""
    text: str
    start: int
    end: int
    category: str  # 'symptom', 'action', 'component', 'negation'
    keyword: str   # 매칭된 키워드
 
@dataclass
class FieldMatches:
    """한 필드에서 발견된 모든 매칭 정보"""
    field_name: str
    text: str
    spans: List[MatchSpan]
   
    def has_category(self, category: str) -> bool:
        """특정 카테고리의 매칭이 있는지 확인"""
        return any(span.category == category for span in self.spans)
   
    def get_category_spans(self, category: str) -> List[MatchSpan]:
        """특정 카테고리의 매칭 스팬들을 반환"""
        return [span for span in self.spans if span.category == category]
 
class KeywordExtractor:
    """키워드 기반 텍스트 매칭 및 추출"""
   
    def __init__(self):
        self.case_sensitive = False
       
    def _create_pattern(self, keywords: List[str]) -> re.Pattern:
        """키워드 리스트로부터 정규식 패턴 생성 (와일드카드 지원)"""
        if not keywords:
            return None
       
        # 키워드를 길이 순으로 정렬 (긴 것부터) - 더 구체적인 매칭 우선
        sorted_keywords = sorted(keywords, key=len, reverse=True)
       
        # 패턴 부분들 생성
        pattern_parts = []
        for keyword in sorted_keywords:
            if keyword.endswith('*'):
                # 와일드카드 패턴: duplicat* → duplicat\w*
                base = re.escape(keyword[:-1])  # '*' 제거 후 이스케이프
                pattern_parts.append(f"{base}\\w*")
            else:
                # 완전 매칭
                pattern_parts.append(re.escape(keyword))
       
        # 단어 경계를 고려한 패턴 생성
        pattern = r'\b(?:' + '|'.join(pattern_parts) + r')\b'
       
        flags = re.IGNORECASE if not self.case_sensitive else 0
        return re.compile(pattern, flags)
   
    def extract_from_text(self, text: str, keywords: List[str], category: str) -> List[MatchSpan]:
        """텍스트에서 키워드를 찾아 MatchSpan 리스트로 반환"""
        if not text or not keywords:
            return []
       
        pattern = self._create_pattern(keywords)
        if not pattern:
            return []
       
        matches = []
        for match in pattern.finditer(text):
            span = MatchSpan(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                category=category,
                keyword=match.group().lower()  # 원래 방식: 매칭된 텍스트를 소문자로
            )
            matches.append(span)
       
        return matches
   
   
    def extract_from_field(self, field_name: str, text: str,
                          symptoms: List[str] = None,
                          actions: List[str] = None,
                          components: List[str] = None,
                          negations: List[str] = None) -> FieldMatches:
        """한 필드에서 모든 카테고리의 키워드를 추출"""
        if not text:
            return FieldMatches(field_name, text or "", [])
       
        all_spans = []
       
        # 각 카테고리별로 키워드 추출
        if symptoms:
            all_spans.extend(self.extract_from_text(text, symptoms, 'symptom'))
       
        if actions:
            all_spans.extend(self.extract_from_text(text, actions, 'action'))
       
        if components:
            all_spans.extend(self.extract_from_text(text, components, 'component'))
       
        if negations:
            all_spans.extend(self.extract_from_text(text, negations, 'negation'))
       
        # 위치순으로 정렬
        all_spans.sort(key=lambda x: x.start)
       
        return FieldMatches(field_name, text, all_spans)
   
    def extract_from_record(self, record: Dict[str, str],
                           symptoms: List[str] = None,
                           actions: List[str] = None,
                           components: List[str] = None,
                           negations: List[str] = None) -> Dict[str, FieldMatches]:
        """전체 레코드에서 모든 필드의 키워드를 추출"""
        results = {}
       
        for field_name, text in record.items():
            field_matches = self.extract_from_field(
                field_name, text, symptoms, actions, components, negations
            )
            results[field_name] = field_matches
       
        return results
   
    def count_unique_matches(self, field_matches: Dict[str, FieldMatches],
                           category: str) -> int:
        """모든 필드에서 특정 카테고리의 유니크한 키워드 개수"""
        unique_keywords = set()
       
        for field_match in field_matches.values():
            for span in field_match.get_category_spans(category):
                unique_keywords.add(span.keyword.lower())
       
        return len(unique_keywords)
   
    def has_any_match(self, field_matches: Dict[str, FieldMatches],
                     category: str) -> bool:
        """모든 필드에서 특정 카테고리의 매칭이 하나라도 있는지 확인"""
        return any(field_match.has_category(category)
                  for field_match in field_matches.values())
   
    def get_match_summary(self, field_matches: Dict[str, FieldMatches]) -> Dict[str, int]:
        """카테고리별 매칭 요약 통계"""
        categories = ['symptom', 'action', 'component', 'negation']
        summary = {}
       
        for category in categories:
            summary[category] = self.count_unique_matches(field_matches, category)
       
        return summary