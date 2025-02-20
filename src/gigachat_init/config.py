# src/gigachat_init/config.py

from src.config import BaseAppSettings
from pydantic import ConfigDict

class GigaChatInitSettings(BaseAppSettings):
    """
    Настройки для сервиса инициализации GigaChat.
    """
    auth_url: str
    auth_header: str
    token_scope: str
    verify_ssl: bool = False
    gigachat_base_url: str

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='GIGACHAT_INIT_'
    )

settings = GigaChatInitSettings()