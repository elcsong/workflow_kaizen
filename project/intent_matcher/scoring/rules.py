"""
룰 기반 점수 계산 모듈
키워드 매칭, 부정 패턴, 조치 힌트 등을 종합한 룰 점수 산정
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from ..extract.keywords import FieldMatches, KeywordExtractor
from ..extract.negation import NegationDetector, NegationContext
 
@dataclass
class RuleScoreComponents:
    """룰 점수의 세부 구성 요소"""
    symptom_score: float
    #-action_score: float
    component_score: float
    negation_penalty: float
    base_score: float
    final_score: float
    details: Dict[str, any]
 
class RuleScorer:
    """룰 기반 점수 계산기"""
   
    def __init__(self):
        self.keyword_extractor = KeywordExtractor()
        self.negation_detector = NegationDetector()
       
        # 기본 점수 가중치
        self.weights = {
            'symptom_base': 0.6,      # 증상 매칭 기본 점수
            'symptom_bonus': 0.2,     # 추가 증상당 보너스
#-            'action_bonus': 0.0,     # 조치 힌트 보너스
            'component_bonus': 0.1,   # 부품 힌트 보너스
        }
       
        # 필드별 가중치
        self.field_weights = {
            'Customers': 0.45,
            'FE': 0.45,
            'Actions': 0.05,
            'Test': 0.05
        }
   
    def calculate_symptom_score(self, field_matches: Dict[str, FieldMatches],
                               required_symptoms: List[str],
                               all_symptoms: List[str]) -> float:
        """증상 매칭 점수 계산"""
        import logging
        
        symptom_matches = {}
        total_weighted_score = 0.0
       
        # 각 필드에서 발견된 증상들을 수집
        for field_name, field_match in field_matches.items():
            field_weight = self.field_weights.get(field_name, 0.1)
            symptom_spans = field_match.get_category_spans('symptom')
           
            field_symptoms = set()
            for span in symptom_spans:
                field_symptoms.add(span.keyword.lower())
           
            symptom_matches[field_name] = field_symptoms
           
            # 필드별 증상 점수 계산
            field_symptom_score = min(1.0, len(field_symptoms) * 0.3)
            total_weighted_score += field_symptom_score * field_weight
       
        # 전체적으로 발견된 유니크한 증상들
        all_found_symptoms = set()
        for symptoms in symptom_matches.values():
            all_found_symptoms.update(symptoms)
       
        # 디버깅: 증상 매칭 정보 로그
        logging.debug(f"[RuleScore Debug] all_symptoms (from config): {all_symptoms}")
        logging.debug(f"[RuleScore Debug] all_found_symptoms (from text): {all_found_symptoms}")
        logging.debug(f"[RuleScore Debug] required_symptoms: {required_symptoms}")
       
        if not all_found_symptoms:
            logging.warning(f"[RuleScore] No symptoms found by KeywordExtractor")
            logging.warning(f"[RuleScore] all_symptoms list was: {all_symptoms}")
            logging.warning(f"[RuleScore] This usually means KeywordExtractor couldn't find any of these keywords in the text")
            return 0.0
       
        # 필수 증상 중 매칭된 것이 있는지 확인 (와일드카드 지원)
        required_lower = [s.lower() for s in required_symptoms]
        has_required = False
        
        for symptom in all_found_symptoms:
            # 기존 로직: 완전 매칭 먼저 확인
            if symptom in required_lower:
                has_required = True
                break
            
            # 와일드카드 매칭 확인
            for required in required_lower:
                if required.endswith('*'):
                    base = required[:-1]  # 별표 제거
                    if symptom.lower().startswith(base):
                        has_required = True
                        break
            
            if has_required:
                break
       
        if not has_required:
            return 0.0  # 필수 증상이 없으면 0점
       
        # 기본 점수 + 추가 증상 보너스
        base_score = self.weights['symptom_base']
        bonus_score = min(len(all_found_symptoms) - 1, 3) * self.weights['symptom_bonus']
        
        final_symptom_score = min(1.0, base_score + bonus_score + total_weighted_score * 0.5)
        
        # 디버깅: 증상 점수 계산 상세
        logging.info(f"[Symptom Score] base_score: {base_score}")
        logging.info(f"[Symptom Score] bonus_score: {bonus_score} (found {len(all_found_symptoms)} symptoms)")
        logging.info(f"[Symptom Score] total_weighted_score: {total_weighted_score:.3f}")
        logging.info(f"[Symptom Score] FINAL symptom_score: {final_symptom_score:.3f}")
        logging.info(f"[Symptom Score] Symptoms by field: {symptom_matches}")
       
        return final_symptom_score
   
    def calculate_component_score(self, field_matches: Dict[str, FieldMatches],
                                component_hints: List[str]) -> float:
        """부품/컴포넌트 힌트 점수 계산"""
        if not component_hints:
            return 0.0
       
        component_matches = 0
        total_weighted_score = 0.0
       
        for field_name, field_match in field_matches.items():
            field_weight = self.field_weights.get(field_name, 0.1)
            component_spans = field_match.get_category_spans('component')
           
            if component_spans:
                component_matches += len(component_spans)
                total_weighted_score += len(component_spans) * field_weight
       
        if component_matches == 0:
            return 0.0
       
        return min(self.weights['component_bonus'], total_weighted_score * 0.2)
   
    def calculate_negation_penalty(self, field_matches: Dict[str, FieldMatches],
                                 treat_resolved_as_match: bool = True) -> float:
        """부정 패턴 감점 계산"""
        all_negations = []
       
        for field_match in field_matches.values():
            negations = self.negation_detector.analyze_field_negations(field_match)
            all_negations.extend(negations)
       
        if not all_negations:
            return 0.0
       
        return self.negation_detector.calculate_negation_penalty(
            all_negations, treat_resolved_as_match
        )
   
    def calculate_symptom_score_fallback(self, record_texts: Dict[str, str],
                                        required_symptoms: List[str]) -> float:
        """
        Fallback 증상 점수 계산: KeywordExtractor 실패 시 직접 텍스트 매칭
        Filter 단계에서 키워드를 찾았는데 RuleScore에서 못 찾는 경우 대비
        """
        import re
        import logging
        
        # 디버깅: record_texts의 필드명과 텍스트 길이 확인
        logging.debug(f"[Fallback Debug] record_texts keys: {list(record_texts.keys())}")
        for fname, txt in record_texts.items():
            txt_len = len(txt) if txt else 0
            preview = txt[:100] if txt else "(empty)"
            logging.debug(f"[Fallback Debug] {fname}: {txt_len} chars, preview: {preview}")
        
        found_symptoms = set()
        field_weights = self.field_weights
        total_weighted_score = 0.0
        
        for field_name, text in record_texts.items():
            if not text:
                continue
                
            text_lower = text.lower()
            field_weight = field_weights.get(field_name, 0.1)
            field_found = set()
            
            for symptom in required_symptoms:
                symptom_lower = symptom.lower()
                
                if symptom_lower.endswith('*'):
                    # 와일드카드: duplicat* → duplicat로 시작하는 단어 찾기
                    base = symptom_lower[:-1]
                    pattern = r'\b' + re.escape(base) + r'\w*\b'
                    matches = re.findall(pattern, text_lower)
                    if matches:
                        logging.debug(f"[Fallback Debug] Found wildcard '{symptom_lower}' matches in {field_name}: {matches}")
                        field_found.update(matches)
                        found_symptoms.update(matches)
                else:
                    # 완전 매칭
                    pattern = r'\b' + re.escape(symptom_lower) + r'\b'
                    if re.search(pattern, text_lower):
                        logging.debug(f"[Fallback Debug] Found exact match '{symptom_lower}' in {field_name}")
                        field_found.add(symptom_lower)
                        found_symptoms.add(symptom_lower)
            
            if field_found:
                field_symptom_score = min(1.0, len(field_found) * 0.3)
                total_weighted_score += field_symptom_score * field_weight
        
        if not found_symptoms:
            logging.warning(f"[RuleScore Fallback] Still no symptoms found in any field")
            logging.warning(f"[RuleScore Fallback] Searched for: {required_symptoms}")
            logging.warning(f"[RuleScore Fallback] Available fields: {list(record_texts.keys())}")
            return 0.0
        
        logging.info(f"[RuleScore Fallback] Found symptoms: {found_symptoms}")
        
        # 기본 점수 + 추가 증상 보너스
        base_score = self.weights['symptom_base']
        bonus_score = min(len(found_symptoms) - 1, 3) * self.weights['symptom_bonus']
        
        return min(1.0, base_score + bonus_score + total_weighted_score * 0.5)
    
    def calculate_rule_score(self, record_texts: Dict[str, str],
                           symptoms: List[str],
                           action_hints: List[str] = None,
                           component_hints: List[str] = None,
                           negation_patterns: List[str] = None,
                           require_symptom: bool = True,
                           treat_resolved_as_match: bool = True) -> RuleScoreComponents:
        """
        전체 룰 점수 계산
       
        Args:
            record_texts: 필드별 텍스트
            symptoms: 증상 키워드들 (required + synonyms)
            action_hints: 조치 힌트 키워드들
            component_hints: 부품 힌트 키워드들
            negation_patterns: 부정 패턴들
            require_symptom: 증상 필수 여부
            treat_resolved_as_match: 해결된 것을 매칭으로 인정할지 여부
        """
        # 키워드 추출
        field_matches = {}
        for field_name, text in record_texts.items():
            field_match = self.keyword_extractor.extract_from_field(
                field_name, text,
                symptoms=symptoms,
                actions=action_hints or [],
                components=component_hints or [],
                negations=negation_patterns or []
            )
            field_matches[field_name] = field_match
       
        # 각 구성 요소별 점수 계산
        # - symptom_score = self.calculate_symptom_score(field_matches, symptoms[:5], symptoms)
        # + TargetConfig.required_any 전체를 반영하도록 수정
        # + (required_symptoms = symptoms에서 필수 세트만 별도로 전달필요)
        import logging
        
        required_symptoms = symptoms  # ← 현재 all_symptoms가 전달되고 있으므로,상위 호출부에서 required 리스트를 함께 넘기는 게 더 정확해요.
        symptom_score = self.calculate_symptom_score(
            field_matches, required_symptoms, symptoms
        )
        
        # Fallback: KeywordExtractor가 증상을 찾지 못한 경우 직접 텍스트 매칭 시도
        if symptom_score == 0.0:
            logging.info(f"[RuleScore] KeywordExtractor found no symptoms, trying fallback method")
            symptom_score = self.calculate_symptom_score_fallback(
                record_texts, required_symptoms
            )
 
#-        action_score = self.calculate_action_score(field_matches, action_hints or [])
        component_score = self.calculate_component_score(field_matches, component_hints or [])
        negation_penalty = self.calculate_negation_penalty(field_matches, treat_resolved_as_match)
       
        # 디버깅: 각 구성 요소 점수 로그
        logging.info(f"[RuleScore Components] symptom_score: {symptom_score:.3f}")
        logging.info(f"[RuleScore Components] component_score: {component_score:.3f}")
        logging.info(f"[RuleScore Components] negation_penalty (raw): {negation_penalty:.3f}")
       
        # 기본 점수 (증상 + 조치 + 부품)
#-        base_score = symptom_score + action_score + component_score
        base_score = symptom_score + component_score
        
        # Negation penalty 완화: 최대 영향을 30%로 제한
        # 원래: final_score = base_score - negation_penalty (너무 가혹함)
        # 수정: final_score = base_score - (negation_penalty * 0.3)
        effective_negation_penalty = negation_penalty * 0.3
        logging.info(f"[RuleScore Components] negation_penalty (effective 30%): {effective_negation_penalty:.3f}")
        
        # 최종 점수 (기본 점수 - 완화된 부정 감점)
        final_score = max(0.0, base_score - effective_negation_penalty)
       
        # 증상 필수 조건 확인
        if require_symptom and symptom_score == 0.0:
            final_score = 0.0
            logging.info(f"[RuleScore] ZERO due to require_symptom=True and symptom_score=0")
        
        # 디버깅: 최종 RuleScore 로그
        logging.info(f"[RuleScore] base_score: {base_score:.3f}")
        logging.info(f"[RuleScore] FINAL RuleScore (final_score): {final_score:.3f}")
       
        # 세부 정보 수집
        details = {
            'field_matches': {name: {
                'symptom_count': len(fm.get_category_spans('symptom')),
                'action_count': len(fm.get_category_spans('action')),
                'component_count': len(fm.get_category_spans('component')),
                'negation_count': len(fm.get_category_spans('negation'))
            } for name, fm in field_matches.items()},
            'negation_summary': self.negation_detector.summarize_negations(field_matches)
        }
       
        return RuleScoreComponents(
            symptom_score=symptom_score,
#-            action_score=action_score,
            component_score=component_score,
            negation_penalty=negation_penalty,
            base_score=base_score,
            final_score=final_score,
            details=details
        )
   
    def get_evidence_spans(self, record_texts: Dict[str, str],
                          symptoms: List[str],
                          action_hints: List[str] = None,
                          component_hints: List[str] = None,
                          negation_patterns: List[str] = None) -> Dict[str, List[str]]:
        """증거가 되는 텍스트 스팬들을 추출"""
        evidence = {
            'symptoms': [],
            'actions': [],
            'components': [],
            'negations': []
        }
       
        for field_name, text in record_texts.items():
            field_match = self.keyword_extractor.extract_from_field(
                field_name, text,
                symptoms=symptoms,
                actions=action_hints or [],
                components=component_hints or [],
                negations=negation_patterns or []
            )
           
            for span in field_match.spans:
                category = span.category
                if category in evidence:
                    context = text[max(0, span.start-20):span.end+20]
                    evidence[category].append(f"{field_name}: ...{context}...")
       
        return evidence