import os
import pytest
from pydantic import ValidationError
from src.llm_search_and_answer.config import LLMServiceSettings

def test_config_loading(monkeypatch):
    # Устанавливаем необходимые переменные окружения
    monkeypatch.setenv("LLM_SERVICE_BASE_URL", "http://testurl")
    monkeypatch.setenv("LLM_SERVICE_MODEL_NAME", "test-model")

    settings = LLMServiceSettings()

    assert settings.base_url == "http://testurl"
    assert settings.model_name == "test-model"

def test_config_missing_fields(monkeypatch):
    # Удаляем переменные окружения, чтобы проверить валидацию
    monkeypatch.delenv("LLM_SERVICE_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_SERVICE_MODEL_NAME", raising=False)
    # Переопределяем конфигурацию, чтобы не подтягивался .env (если он существует)
    monkeypatch.setattr(LLMServiceSettings, "model_config", {"env_file": "nonexistent.env", "env_prefix": "LLM_SERVICE_"})

    with pytest.raises(ValidationError):
        _ = LLMServiceSettings()
