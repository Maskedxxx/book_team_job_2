# src/book_parser/config.py

from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Путь к файлу с картой знаний
    know_map_path: str = "data/knowledge_maps/goldsmith/know_map_full.json"
    # Путь к файлу с распарсенной книгой
    kniga_path: str = "data/row/goldsmith/kniga_full_content.json"

    model_config = ConfigDict(
        env_file='.env'
    )

# Экземпляр настроек, который можно импортировать в другие модули
settings = Settings()
