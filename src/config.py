# src/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List

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
    
    # Список подглав для LLM анализа
    available_subchapters: List[str] = [
        '3.11.1', '3.11.2', '3.11.3', '3.12.1', '3.12.2'
    ]

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='',
    )

settings = ServicePortsSettings()
