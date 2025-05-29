# src/book_parser/services.py

import json
from pathlib import Path
from typing import Any, Dict
from src.book_parser.config import settings
from src.book_parser.parsers.content_parts_parser import ContentPartsParser
from src.book_parser.parsers.chapter_parser import ChapterParser
from src.book_parser.parsers.subchapter_parser import SubchapterParser
from src.book_parser.parsers.page_content_parser import PageContentParser
from src.utils.logger import get_logger

logger = get_logger("book_parser")

def load_json(file_path: Path) -> Dict[str, Any]:
    """
    Загружает JSON данные из указанного файла.

    Args:
        file_path (Path): Путь к JSON файлу.

    Returns:
        dict: Загруженные данные.
    """
    try:
        logger.debug(f"Загрузка JSON: {file_path.name}")
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"JSON загружен успешно")
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки {file_path.name}: {e}")
        raise

def get_parts():
    """
    Получает список частей книги с использованием ContentPartsParser.

    Returns:
        List[PartOutput]: Список моделей частей книги.
    """
    know_map_path = Path(settings.know_map_path)
    know_map_data = load_json(know_map_path)
    parser = ContentPartsParser(know_map_data)
    parts = parser.parse_parts()
    logger.info(f"Получено {len(parts)} частей книги")
    return parts

def get_chapters_by_part(part_number: int):
    """
    Получает список глав для указанной части книги с использованием ChapterParser.

    Args:
        part_number (int): Номер части книги.

    Returns:
        List[ChapterOutput]: Список моделей глав книги.
    """
    know_map_path = Path(settings.know_map_path)
    know_map_data = load_json(know_map_path)
    parser = ChapterParser(know_map_data)
    chapters = parser.parse_chapters_by_part(part_number)
    logger.info(f"Для части {part_number} найдено {len(chapters)} глав")
    return chapters

def get_subchapters_by_chapter(part_number: int, chapter_number: int):
    """
    Получает список подглав для указанной главы книги с использованием SubchapterParser.

    Args:
        part_number (int): Номер части книги.
        chapter_number (int): Номер главы книги.

    Returns:
        List[SubchapterOutput]: Список моделей подглав книги.
    """
    know_map_path = Path(settings.know_map_path)
    know_map_data = load_json(know_map_path)
    parser = SubchapterParser(know_map_data)
    subchapters = parser.parse_subchapters_by_chapter(part_number, chapter_number)
    logger.info(f"Для части {part_number}, главы {chapter_number} найдено {len(subchapters)} подглав")
    return subchapters

def get_page_content(subchapter_number: str):
    """
    Получает содержимое страниц для выбранной подглавы книги с использованием PageContentParser.

    Args:
        subchapter_number (str): Номер подглавы книги.

    Returns:
        PageContentOutput: Модель с содержимом страниц.
    """
    know_map_path = Path(settings.know_map_path)
    kniga_path = Path(settings.kniga_path)
    know_map_data = load_json(know_map_path)
    kniga_data = load_json(kniga_path)
    parser = PageContentParser(know_map_data, kniga_data)
    content = parser.parse_final_content(subchapter_number)
    logger.info(f"Получен контент подглавы {subchapter_number}: {len(content.pages)} страниц")
    return content