# src/llm_search_and_answer/config.py
from src.config import BaseAppSettings
from pydantic import ConfigDict

class LLMServiceSettings(BaseAppSettings):
    """
    Настройки для сервиса поиска и ответов.
    """
    base_url: str
    model_name: str

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='LLM_SERVICE_'
    )

settings = LLMServiceSettings()