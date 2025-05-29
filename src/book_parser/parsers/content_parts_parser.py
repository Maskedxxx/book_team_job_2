from typing import List, Dict, Any
from src.book_parser.models import PartOutput
from src.utils.logger import get_logger

class ContentPartsParser:
    """
    Класс для парсинга частей книги из JSON-структуры.

    Ожидаемый формат JSON:
    {
        "content": {
            "parts": [
                {
                    "title": "...",
                    "summary": "...",
                    "key_points": [...],
                    "part_number": ... 
                },
                ...
            ]
        }
    }
    """
    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data
        self.logger = get_logger(__name__)

    def to_model(self, part: Dict[str, Any]) -> PartOutput:
        """
        Преобразует словарь с данными части в модель PartOutput.
        Логгирует имя заголовка (title) распарсенной части.
        """
        key_points = part.get("key_points", [])
        key_points_str = ", ".join(str(point) for point in key_points) if isinstance(key_points, list) else str(key_points)
        model = PartOutput(
            part_number=str(part.get("part_number", "Не указан номер")),
            title=part.get("title", "Нет заголовка"),
            summary=part.get("summary", "Нет описания"),
            key_points=key_points_str
        )
        self.logger.debug(f"Распарсена часть: {model.title}")
        return model

    def parse_parts(self) -> List[PartOutput]:
        """
        Парсит список частей книги и возвращает список моделей PartOutput.
        Логгирует список заголовков всех распарсенных частей.
        """
        parts = self.data.get("content", {}).get("parts", [])
        models = [self.to_model(part) for part in parts]
        part_titles = [model.title for model in models]
        self.logger.debug(f"Успешно распарсены части: {part_titles}")
        return models
