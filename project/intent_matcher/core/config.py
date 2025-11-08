"""
Target configuration loader and validator
"""
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
 
class TargetConfig:
    """타겟 불량 유형 설정을 로드하고 관리하는 클래스"""
   
    def __init__(self, config_path: str):
        """
        Args:
            config_path: YAML 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self._config = self._load_config()
        self._validate_config()
   
    def _load_config(self) -> Dict[str, Any]:
        """YAML 설정 파일을 로드"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
       
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
   
    def _validate_config(self):
        """설정 파일의 필수 항목들을 검증"""
        required_fields = ['id', 'name', 'symptoms', 'policy']
        for field in required_fields:
            if field not in self._config:
                raise ValueError(f"Missing required field: {field}")
       
        # symptoms 검증
        symptoms = self._config.get('symptoms', {})
        if 'required_any' not in symptoms:
            raise ValueError("Missing 'required_any' in symptoms")
       
        # policy 검증
        policy = self._config.get('policy', {})
        required_policy_fields = ['require_symptom', 'min_score', 'review_band']
        for field in required_policy_fields:
            if field not in policy:
                raise ValueError(f"Missing required policy field: {field}")
   
    @property
    def id(self) -> str:
        return self._config['id']
   
    @property
    def name(self) -> str:
        return self._config['name']
   
    @property
    def symptoms(self) -> Dict[str, List[str]]:
        return self._config['symptoms']
   
    @property
    def required_symptoms(self) -> List[str]:
        return self.symptoms.get('required_any', [])
   
    @property
    def symptom_synonyms(self) -> List[str]:
        return self.symptoms.get('synonyms', [])
   
    @property
    def all_symptoms(self) -> List[str]:
        """모든 증상 키워드 (필수 + 동의어)"""
        return self.required_symptoms + self.symptom_synonyms
   
    @property
    def negation_patterns(self) -> List[str]:
        return self._config.get('negation_patterns', [])
   
    # Action Hints 사용 중단: 필드 자체 제거
    #-@property
    #-def action_hints(self) -> List[str]:
    #-    return self._config.get('action_hints', [])
    @property
    def action_hints(self) -> List[str]:
        return []  # 항상 빈 리스트 반환 (과거 설정이 있어도 무시)
   
   
    @property
    def component_hints(self) -> List[str]:
        return self._config.get('component_hints', [])
   
    @property
    def confusers(self) -> List[str]:
        return self._config.get('confusers', [])
   
    @property
    def policy(self) -> Dict[str, Any]:
        return self._config['policy']
   
    @property
    def require_symptom(self) -> bool:
        return self.policy.get('require_symptom', True)
   
    @property
    def min_score(self) -> float:
        return self.policy.get('min_score', 0.6)
   
    @property
    def review_band(self) -> List[float]:
        return self.policy.get('review_band', [0.55, 0.60])
   
    @property
    def treat_resolved_as_match(self) -> bool:
        return self.policy.get('treat_resolved_as_match', True)
   
    @property
    def codes(self) -> Dict[str, Any]:
        return self._config.get('codes', {})
   
    def __repr__(self) -> str:
        return f"TargetConfig(id='{self.id}', name='{self.name}')"