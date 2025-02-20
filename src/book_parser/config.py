# src/book_parser/config.py

from src.config import BaseAppSettings
from pydantic import ConfigDict

class BookParserSettings(BaseAppSettings):
    """
    Настройки для сервиса парсинга книг.
    """

    know_map_path: str 
    kniga_path: str

    model_config = ConfigDict(
        env_file='.env',
        env_prefix='BOOK_PARSER_'
    )

# Экземпляр настроек, который можно импортировать в другие модули
settings = BookParserSettings()
