# src/book_parser/routes.py

from fastapi import APIRouter, HTTPException
from typing import Dict
from src.book_parser.services import (
    get_parts,
    get_chapters_by_part,
    get_subchapters_by_chapter,
    get_page_content,
)
from src.book_parser.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/parser", tags=["book_parser"])

@router.get("/parts", response_model=Dict)
def parts() -> Dict:
    """
    Эндпоинт для получения списка частей книги.
    """
    try:
        logger.info("Запрос списка частей книги")
        parts_data = get_parts()
        return {"parts": parts_data}
    except Exception as e:
        logger.error(f"Ошибка при получении частей книги: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parts/{part_number}/chapters", response_model=Dict)
def chapters(part_number: int) -> Dict:
    """
    Эндпоинт для получения списка глав для выбранной части книги.

    Args:
        part_number (int): Номер части книги.
    """
    try:
        logger.info(f"Запрос глав для части {part_number}")
        chapters_data = get_chapters_by_part(part_number)
        return {"chapters": chapters_data}
    except Exception as e:
        logger.error(f"Ошибка при получении глав для части {part_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parts/{part_number}/chapters/{chapter_number}/subchapters", response_model=Dict)
def subchapters(part_number: int, chapter_number: int) -> Dict:
    """
    Эндпоинт для получения списка подглав для выбранной главы книги.

    Args:
        part_number (int): Номер части книги.
        chapter_number (int): Номер главы книги.
    """
    try:
        logger.info(f"Запрос подглав для части {part_number}, главы {chapter_number}")
        subchapters_data = get_subchapters_by_chapter(part_number, chapter_number)
        return {"subchapters": subchapters_data}
    except Exception as e:
        logger.error(f"Ошибка при получении подглав для части {part_number}, главы {chapter_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subchapters/{subchapter_number}/content", response_model=Dict)
def content(subchapter_number: str) -> Dict:
    """
    Эндпоинт для получения содержимого страниц для выбранной подглавы книги.

    Args:
        subchapter_number (str): Номер подглавы книги.
    """
    try:
        logger.info(f"Запрос содержимого для подглавы {subchapter_number}")
        content_data = get_page_content(subchapter_number)
        return {"content": content_data}
    except Exception as e:
        logger.error(f"Ошибка при получении содержимого для подглавы {subchapter_number}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
