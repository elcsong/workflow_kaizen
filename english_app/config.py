"""환경 설정 로딩과 API 키 검증."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "english_app" / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
AUDIO_DIR = DATA_DIR / "audio"

OLLAMA_ENDPOINT = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_DEFAULT_MODEL = "gemma4:26b"
OLLAMA_FALLBACK_MODELS: tuple[str, ...] = ("gemma4:26b", "gpt-oss:latest")

API_KEY_ENV_VARS: dict[str, str] = {
    "OpenAI": "OPENAI_API_KEY",
    "Gemini": "GEMINI_API_KEY",
    "Anthropic": "CLAUDE_API_KEY",
}


@dataclass(frozen=True)
class ProviderAvailability:
    provider: str
    available: bool
    reason: str | None = None


def load_environment(env_file: Path | None = None) -> None:
    """`.env` 파일을 로드한다. python-dotenv 미설치 시 로그만 남긴다."""
    if load_dotenv is None:
        logger.warning("python-dotenv 미설치 — OS 환경변수만 사용")
        return
    env_path = env_file or PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("환경변수 로드: %s", env_path)
    else:
        logger.info(".env 파일 없음 — OS 환경변수만 사용")


def check_cloud_provider_keys() -> list[ProviderAvailability]:
    """클라우드 Provider API 키 유무를 앱 시작 시점에 점검."""
    results: list[ProviderAvailability] = []
    for provider, env_var in API_KEY_ENV_VARS.items():
        key = os.environ.get(env_var)
        if key:
            results.append(ProviderAvailability(provider, True))
        else:
            results.append(
                ProviderAvailability(provider, False, reason=f"{env_var} 미설정")
            )
    return results
