# src/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class BaseAppSettings(BaseSettings):
    model_config = ConfigDict(
        env_file='.env',
        extra='allow'
    )

class ServicePortsSettings(BaseAppSettings):
    gigachat_init_port: int
    book_parser_port: int
    llm_service_port: int
    google_sheets_port: int

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='',  # Без префикса для простоты чтения
    )

settings = ServicePortsSettings()
