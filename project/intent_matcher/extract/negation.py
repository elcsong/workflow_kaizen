"""
부정 패턴 감지 및 컨텍스트 분석 모듈
"not reproducible", "resolved", "passed all tests" 등의 부정적 문맥을 감지
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from .keywords import MatchSpan, FieldMatches
 
@dataclass
class NegationContext:
    """부정 문맥 정보"""
    pattern: str
    span: MatchSpan
    severity: float  # 0.0 ~ 1.0, 높을수록 강한 부정
    context_type: str  # 'resolution', 'non_reproduction', 'normal_operation'
 
class NegationDetector:
    """부정 패턴 감지 및 분석"""
   
    def __init__(self):
        # 부정 패턴을 심각도별로 분류
        self.negation_patterns = {
            'resolution': {
                'patterns': [
                    r'\bresolved\b',
                    r'\bfixed\b',
                    r'\brepaired\b',
                    r'\bcorrected\b',
                    r'\bsolved\b',
                    r'\bworking\s+(?:properly|correctly|fine|well)\b',
                    r'\bfunctioning\s+(?:properly|correctly|normally)\b',
                    r'\bback\s+to\s+normal\b',
                    r'\bno\s+longer\s+(?:an\s+)?issue\b'
                ],
                'severity': 0.3  # 해결된 것은 중간 정도 부정 (정책에 따라 매칭으로 인정할 수도)
            },
            'non_reproduction': {
                'patterns': [
                    r'\bnot\s+reproducible\b',
                    r'\bcannot\s+reproduce\b',
                    r'\bunable\s+to\s+reproduce\b',
                    r'\bno\s+issue\s+found\b',
                    r'\bno\s+problem\s+detected\b',
                    r'\bno\s+fault\s+found\b'
                ],
                'severity': 0.8  # 재현 불가는 강한 부정
            },
            'normal_operation': {
                'patterns': [
                    r'\bpassed\s+all\s+tests\b',
                    r'\bwithin\s+normal\s+limits\b',
                    r'\bnormal\s+operation\b',
                    r'\bno\s+(?:issues?|problems?)\b',
                    r'\bfunctioning\s+normally\b',
                    r'\boperating\s+normally\b',
                    r'\bno\s+defects?\s+found\b'
                ],
                'severity': 0.9  # 정상 동작은 매우 강한 부정
            }
        }
   
    def _compile_patterns(self) -> Dict[str, List[Tuple[re.Pattern, float]]]:
        """정규식 패턴들을 컴파일"""
        compiled = {}
       
        for context_type, info in self.negation_patterns.items():
            patterns = []
            for pattern_str in info['patterns']:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                patterns.append((pattern, info['severity']))
            compiled[context_type] = patterns
       
        return compiled
   
    def detect_negations(self, text: str) -> List[NegationContext]:
        """텍스트에서 부정 패턴들을 감지"""
        if not text:
            return []
       
        compiled_patterns = self._compile_patterns()
        negations = []
       
        for context_type, patterns in compiled_patterns.items():
            for pattern, severity in patterns:
                for match in pattern.finditer(text):
                    span = MatchSpan(
                        text=match.group(),
                        start=match.start(),
                        end=match.end(),
                        category='negation',
                        keyword=match.group().lower()
                    )
                   
                    negation = NegationContext(
                        pattern=pattern.pattern,
                        span=span,
                        severity=severity,
                        context_type=context_type
                    )
                    negations.append(negation)
       
        # 위치순으로 정렬
        negations.sort(key=lambda x: x.span.start)
        return negations
   
    def analyze_field_negations(self, field_matches: FieldMatches) -> List[NegationContext]:
        """필드의 부정 패턴을 분석"""
        return self.detect_negations(field_matches.text)
   
    def calculate_negation_penalty(self, negations: List[NegationContext],
                                 treat_resolved_as_match: bool = True) -> float:
        """부정 패턴들로부터 감점을 계산"""
        if not negations:
            return 0.0
       
        total_penalty = 0.0
       
        for negation in negations:
            penalty = negation.severity
           
            # 해결된 것을 매칭으로 인정하는 정책인 경우 감점 완화
            if (treat_resolved_as_match and
                negation.context_type == 'resolution'):
                penalty *= 0.3  # 해결 관련 감점을 크게 줄임
           
            total_penalty += penalty
       
        # 최대 감점 제한 (너무 많은 부정이 있어도 일정 수준에서 제한)
        return min(total_penalty, 1.0)
   
    def get_strongest_negation(self, negations: List[NegationContext]) -> Optional[NegationContext]:
        """가장 강한 부정 패턴을 반환"""
        if not negations:
            return None
       
        return max(negations, key=lambda x: x.severity)
   
    def has_resolution_context(self, negations: List[NegationContext]) -> bool:
        """해결 관련 문맥이 있는지 확인"""
        return any(neg.context_type == 'resolution' for neg in negations)
   
    def has_non_reproduction_context(self, negations: List[NegationContext]) -> bool:
        """재현 불가 문맥이 있는지 확인"""
        return any(neg.context_type == 'non_reproduction' for neg in negations)
   
    def summarize_negations(self, field_matches_dict: Dict[str, FieldMatches]) -> Dict[str, any]:
        """전체 레코드의 부정 패턴을 요약"""
        all_negations = []
        field_negation_counts = {}
       
        for field_name, field_matches in field_matches_dict.items():
            negations = self.analyze_field_negations(field_matches)
            all_negations.extend(negations)
            field_negation_counts[field_name] = len(negations)
       
        return {
            'total_negations': len(all_negations),
            'field_counts': field_negation_counts,
            'has_resolution': self.has_resolution_context(all_negations),
            'has_non_reproduction': self.has_non_reproduction_context(all_negations),
            'strongest_negation': self.get_strongest_negation(all_negations),
            'max_severity': max([neg.severity for neg in all_negations]) if all_negations else 0.0
        }