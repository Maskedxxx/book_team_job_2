import pytest
from pathlib import Path
from src.book_parser.services import load_json, get_parts, get_chapters_by_part
from src.book_parser.config import settings

@pytest.fixture
def test_json_data():
    """Фикстура с тестовыми данными для JSON"""
    return {
        "content": {
            "parts": [
                {
                    "part_number": 1,
                    "title": "Тестовая часть",
                    "summary": "Тестовое описание",
                    "key_points": ["point1", "point2"],
                    "chapters": [
                        {
                            "chapter_number": 1,
                            "title": "Тестовая глава",
                            "summary": "Описание главы",
                            "key_points": ["point1", "point2"]
                        }
                    ]
                }
            ]
        }
    }

@pytest.fixture
def test_json_file(tmp_path, test_json_data):
    """Фикстура для создания временного JSON файла"""
    import json
    file_path = tmp_path / "test_know_map.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(test_json_data, f)
    return file_path

def test_load_json(test_json_file):
    """Проверка загрузки JSON файла"""
    data = load_json(test_json_file)
    assert isinstance(data, dict)
    assert "content" in data
    assert "parts" in data["content"]

def test_load_json_file_not_found():
    """Проверка обработки ошибки при отсутствии файла"""
    with pytest.raises(Exception):
        load_json(Path("non_existent.json"))

def test_get_parts(monkeypatch, test_json_data):
    """Проверка получения списка частей"""
    def mock_load_json(file_path):
        return test_json_data
    
    monkeypatch.setattr("src.book_parser.services.load_json", mock_load_json)
    
    parts = get_parts()
    assert len(parts) > 0
    assert parts[0].title == "Тестовая часть"
    assert parts[0].part_number == "1"

def test_get_chapters(monkeypatch, test_json_data):
    """Проверка получения списка глав"""
    def mock_load_json(file_path):
        return test_json_data
    
    monkeypatch.setattr("src.book_parser.services.load_json", mock_load_json)
    
    chapters = get_chapters_by_part(1)
    assert len(chapters) > 0
    assert chapters[0].title == "Тестовая глава"
    assert chapters[0].chapter_number == "1"