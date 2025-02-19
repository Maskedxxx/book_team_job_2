import pytest
from fastapi.testclient import TestClient
from src.book_parser.main import app

client = TestClient(app)

def test_get_parts():
    """Проверка доступности эндпоинта получения частей книги"""
    response = client.get("/parser/parts")
    assert response.status_code == 200
    assert "parts" in response.json()

def test_get_chapters():
    """Проверка доступности эндпоинта получения глав для части"""
    response = client.get("/parser/parts/1/chapters")
    assert response.status_code == 200
    assert "chapters" in response.json()

def test_get_subchapters():
    """Проверка доступности эндпоинта получения подглав"""
    response = client.get("/parser/parts/1/chapters/1/subchapters")
    assert response.status_code == 200
    assert "subchapters" in response.json()

def test_get_content():
    """Проверка доступности эндпоинта получения содержимого"""
    response = client.get("/parser/subchapters/1.1.1/content")
    assert response.status_code == 200
    assert "content" in response.json()