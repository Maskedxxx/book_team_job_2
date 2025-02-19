# src/book_parser/models.py

from pydantic import BaseModel
from typing import Optional

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

class PageContentOutput(BaseModel):
    """
    Модель для представления содержимого страниц книги.
    """
    content: str
