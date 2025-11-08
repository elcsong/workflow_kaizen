"""
정책 관리 및 적용 모듈
임계값, 리뷰 밴드, 특수 규칙 등의 정책을 관리
"""
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass
from ..core.config import TargetConfig
 
@dataclass
class PolicySettings:
    """정책 설정"""
    require_symptom: bool = True
    min_score: float = 0.6
    review_band: tuple = (0.55, 0.60)
    treat_resolved_as_match: bool = True
    alpha: float = 0.5  # 룰 vs 의미 점수 가중치
    field_weights: Dict[str, float] = None
   
    def __post_init__(self):
        if self.field_weights is None:
            self.field_weights = {
                'Customers': 0.45,
                'FE': 0.45,
                'Actions': 0.05,
                'Test': 0.05
            }
 
class PolicyManager:
    """정책 관리자"""
   
    def __init__(self, target_config: TargetConfig = None):
        """
        Args:
            target_config: 타겟 설정 (있는 경우 정책을 여기서 로드)
        """
        self.target_config = target_config
        self.default_settings = PolicySettings()
       
        # 타겟 설정에서 정책 로드
        if target_config:
            self.settings = self._load_from_config(target_config)
        else:
            self.settings = self.default_settings
   
    def _load_from_config(self, config: TargetConfig) -> PolicySettings:
        """타겟 설정에서 정책 설정을 로드"""
        policy = config.policy
       
        review_band = policy.get('review_band', [0.55, 0.60])
        if isinstance(review_band, list) and len(review_band) >= 2:
            review_band = (review_band[0], review_band[1])
        else:
            review_band = (0.55, 0.60)
       
        return PolicySettings(
            require_symptom=config.require_symptom,
            min_score=config.min_score,
            review_band=review_band,
            treat_resolved_as_match=config.treat_resolved_as_match,
            alpha=0.5,  # 기본값, 추후 설정에서 로드 가능
            field_weights=self.default_settings.field_weights
        )
   
    def update_settings(self, **kwargs) -> None:
        """정책 설정 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
   
    def update_thresholds(self,
                         min_score: Optional[float] = None,
                         review_band: Optional[Union[Tuple[float, float], List[float]]] = None,
                         require_symptom: Optional[bool] = None,
                         alpha: Optional[float] = None,
                         treat_resolved_as_match: Optional[bool] = None) -> None:
        """임계값들을 개별적으로 업데이트
       
        Args:
            min_score: 최소 임계점
            review_band: 리뷰 구간 (tuple 또는 list)
            require_symptom: 증상 필수 여부
            alpha: 룰 vs 의미 점수 가중치
            treat_resolved_as_match: 해결된 케이스 매칭 여부
        """
        if min_score is not None:
            if not 0.0 <= min_score <= 1.0:
                raise ValueError(f"min_score must be between 0.0 and 1.0, got {min_score}")
            self.settings.min_score = min_score
       
        if review_band is not None:
            if isinstance(review_band, list):
                review_band = tuple(review_band)
            if len(review_band) != 2 or review_band[0] >= review_band[1]:
                raise ValueError(f"review_band must be (lower, upper) with lower < upper, got {review_band}")
            self.settings.review_band = review_band
       
        if require_symptom is not None:
            self.settings.require_symptom = require_symptom
       
        if alpha is not None:
            if not 0.0 <= alpha <= 1.0:
                raise ValueError(f"alpha must be between 0.0 and 1.0, got {alpha}")
            self.settings.alpha = alpha
       
        if treat_resolved_as_match is not None:
            self.settings.treat_resolved_as_match = treat_resolved_as_match
   
    def batch_update(self, updates: Dict[str, Any]) -> None:
        """배치로 여러 설정을 동시에 업데이트"""
        self.update_thresholds(**updates)
   
    def get_field_weight(self, field_name: str) -> float:
        """필드별 가중치 반환"""
        return self.settings.field_weights.get(field_name, 0.1)
   
    def is_score_above_threshold(self, score: float) -> bool:
        """점수가 임계값 이상인지 확인"""
        return score >= self.settings.min_score
   
    def is_in_review_band(self, score: float) -> bool:
        """점수가 리뷰 밴드 내에 있는지 확인"""
        return self.settings.review_band[0] <= score < self.settings.review_band[1]
   
    def should_require_symptom(self, symptom_score: float) -> bool:
        """증상 필수 조건을 만족하는지 확인"""
        if not self.settings.require_symptom:
            return True
        return symptom_score > 0.0
   
    def apply_special_rules(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        """특수 규칙 적용"""
        adjustments = {}
       
        # 해결된 케이스에 대한 특별 처리
        if self.settings.treat_resolved_as_match:
            negation_summary = analysis_context.get('negation_summary', {})
            if negation_summary.get('has_resolution', False):
                adjustments['resolution_bonus'] = 0.1
                adjustments['reasoning_append'] = ' (해결된 케이스로 인정)'
       
        # 높은 품질의 필드 데이터가 있는 경우 보너스
        field_quality = analysis_context.get('field_quality', {})
        high_quality_fields = sum(1 for quality in field_quality.values() if quality > 0.8)
        if high_quality_fields >= 3:
            adjustments['quality_bonus'] = 0.05
       
        # 매우 강한 부정 신호가 있는 경우 추가 감점
        max_negation_severity = analysis_context.get('max_negation_severity', 0.0)
        if max_negation_severity > 0.9:
            adjustments['strong_negation_penalty'] = 0.1
       
        return adjustments
   
    def validate_settings(self) -> List[str]:
        """정책 설정의 유효성 검증"""
        issues = []
       
        if not 0.0 <= self.settings.min_score <= 1.0:
            issues.append(f"min_score must be between 0.0 and 1.0, got {self.settings.min_score}")
       
        if not 0.0 <= self.settings.alpha <= 1.0:
            issues.append(f"alpha must be between 0.0 and 1.0, got {self.settings.alpha}")
       
        review_low, review_high = self.settings.review_band
        if review_low >= review_high:
            issues.append(f"review_band lower bound must be less than upper bound")
       
        if review_high > self.settings.min_score:
            issues.append(f"review_band upper bound should not exceed min_score")
       
        # 필드 가중치 합계 확인
        total_weight = sum(self.settings.field_weights.values())
        if abs(total_weight - 1.0) > 0.1:
            issues.append(f"field_weights should sum to approximately 1.0, got {total_weight}")
       
        return issues
   
    def get_decision_thresholds(self) -> Dict[str, float]:
        """의사결정 임계값들 반환"""
        return {
            'min_score': self.settings.min_score,
            'review_lower': self.settings.review_band[0],
            'review_upper': self.settings.review_band[1],
            'alpha': self.settings.alpha
        }
   
    def export_settings(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 내보내기"""
        return {
            'require_symptom': self.settings.require_symptom,
            'min_score': self.settings.min_score,
            'review_band': list(self.settings.review_band),
            'treat_resolved_as_match': self.settings.treat_resolved_as_match,
            'alpha': self.settings.alpha,
            'field_weights': self.settings.field_weights.copy()
        }
   
    def import_settings(self, settings_dict: Dict[str, Any]) -> None:
        """딕셔너리에서 설정 가져오기"""
        for key, value in settings_dict.items():
            if key == 'review_band' and isinstance(value, list):
                value = tuple(value)
           
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
   
    def load_from_cli_args(self, cli_args: Dict[str, Any]) -> None:
        """CLI 인수에서 임계값 설정 로드
       
        Args:
            cli_args: CLI에서 파싱된 인수들
        """
        cli_mapping = {
            'min_score': 'min_score',
            'review_band': 'review_band',
            'require_symptom': 'require_symptom',
            'alpha': 'alpha',
            'treat_resolved_as_match': 'treat_resolved_as_match'
        }
       
        updates = {}
        for cli_key, setting_key in cli_mapping.items():
            if cli_key in cli_args and cli_args[cli_key] is not None:
                updates[setting_key] = cli_args[cli_key]
       
        if updates:
            self.update_thresholds(**updates)
   
    def get_current_config_summary(self) -> Dict[str, Any]:
        """현재 설정 상태의 요약 정보 반환"""
        return {
            'policy_settings': {
                'min_score': self.settings.min_score,
                'review_band': list(self.settings.review_band),
                'require_symptom': self.settings.require_symptom,
                'alpha': self.settings.alpha,
                'treat_resolved_as_match': self.settings.treat_resolved_as_match
            },
            'field_weights': self.settings.field_weights.copy(),
            'validation_status': len(self.validate_settings()) == 0,
            'decision_thresholds': self.get_decision_thresholds()
        }
   
    def reset_to_defaults(self) -> None:
        """설정을 기본값으로 리셋"""
        self.settings = PolicySettings()
   
    def create_cli_help_text(self) -> str:
        """CLI 도움말 텍스트 생성"""
        return f"""
임계값 설정 옵션:
  --min-score FLOAT     최소 임계점 (기본값: {self.default_settings.min_score})
  --review-band FLOAT,FLOAT  리뷰 구간 하한,상한 (기본값: {self.default_settings.review_band[0]},{self.default_settings.review_band[1]})
  --require-symptom BOOL      증상 필수 여부 (기본값: {self.default_settings.require_symptom})
  --alpha FLOAT         룰 vs 의미 점수 가중치 (기본값: {self.default_settings.alpha})
  --treat-resolved-as-match BOOL  해결된 케이스 매칭 여부 (기본값: {self.default_settings.treat_resolved_as_match})
 
예시:
  --min-score 0.7 --review-band 0.6,0.7 --require-symptom false
        """