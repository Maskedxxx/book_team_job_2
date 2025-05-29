# src/book_parser/models.py

from pydantic import BaseModel
from typing import Optional, List


class PartOutput(BaseModel):
    """
    Модель для представления информации о части книги.
    """
    part_number: Optional[str]
    title: str
    summary: str
    key_points: str

class ChapterOutput(BaseModel):
    """
    Модель для представления информации о главе книги.
    """
    chapter_number: Optional[str]
    title: str
    summary: str
    key_points: str

class SubchapterOutput(BaseModel):
    """
    Модель для представления информации о подглаве книги.
    """
    subchapter_number: Optional[str]
    title: str
    summary: str
    key_points: str

class PageMetadata(BaseModel):
    """
    Модель для представления метаданных отдельной страницы.
    """
    page_number: int
    content: str
    summary: str

class PageContentOutput(BaseModel):
    """
    Модель для представления содержимого подглавы книги,
    включающая заголовок подглавы и список страниц с их метаданными.
    """
    subchapter_title: str
    pages: List[PageMetadata]
